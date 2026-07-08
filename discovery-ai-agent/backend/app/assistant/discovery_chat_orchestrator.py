from app.assistant.assistant_action_builder import AssistantActionBuilder
from app.assistant.assistant_response_builder import AssistantResponseBuilder
from app.assistant.chat_context_assembler import ChatContextAssembler
from app.assistant.intent_router import IntentRouter, RoutedIntent
from app.agents.runtime import StageProcessorResult, ToolAction, ToolPolicy
from app.agents.runtime.stage_processor_contract import StageProcessorRequest
from app.models.discovery import ArtifactType, DiscoveryProject
from app.processors import processor_for_artifact
from app.rag.simple_retriever import RetrievalQuery, SimpleRetriever


class DiscoveryChatOrchestrator:
    def __init__(
        self,
        intent_router: IntentRouter | None = None,
        tool_policy: ToolPolicy | None = None,
        retriever: SimpleRetriever | None = None,
        context_assembler: ChatContextAssembler | None = None,
        response_builder: AssistantResponseBuilder | None = None,
        action_builder: AssistantActionBuilder | None = None,
    ):
        self.intent_router = intent_router or IntentRouter()
        self.tool_policy = tool_policy or ToolPolicy.for_ai_discovery_chat()
        self.retriever = retriever or SimpleRetriever()
        self.context_assembler = context_assembler or ChatContextAssembler()
        self.response_builder = response_builder or AssistantResponseBuilder()
        self.action_builder = action_builder or AssistantActionBuilder()

    def handle_message(
        self,
        *,
        project: DiscoveryProject,
        message: str,
        artifact_type: ArtifactType | None = None,
        context: dict | None = None,
        context_artifact: dict | None = None,
        artifacts: dict | None = None,
    ) -> dict:
        intent = self.intent_router.route(message, artifact_type)
        if intent.intent_type in {"draft_artifact_patch", "validate_workflow"} and intent.target_artifact_type:
            result = self._draft_patch(project, message, intent, context_artifact or {}, artifacts or {})
        else:
            result = self.response_builder.guidance_response(
                intent_type=intent.intent_type,
                confidence=intent.confidence,
                artifact_type=intent.target_artifact_type,
            )
        return {
            "intent": {
                "type": intent.intent_type,
                "target_artifact_type": intent.target_artifact_type.value if intent.target_artifact_type else None,
                "confidence": intent.confidence,
                "command": intent.command,
                "prompt_version": intent.prompt_version,
            },
            "result": result,
        }

    def _draft_patch(
        self,
        project: DiscoveryProject,
        message: str,
        intent: RoutedIntent,
        context_artifact: dict,
        artifacts: dict,
    ) -> StageProcessorResult:
        artifact_type = intent.target_artifact_type
        if artifact_type is None:
            raise ValueError("target artifact type is required")
        for action_name in ("proposed_patch.create", "patch.preview"):
            if not self.tool_policy.is_allowed(ToolAction(name=action_name, target=artifact_type.value)):
                return self.response_builder.policy_denied_response(
                    artifact_type=artifact_type,
                    intent_type=intent.intent_type,
                    action_name=action_name,
                )

        retrieval_result = self.retriever.retrieve(
            RetrievalQuery(
                project_id=project.id,
                query=self._retrieval_query(message, artifact_type),
                artifact_type=artifact_type.value,
                stage=artifact_type.value,
                context_artifact=context_artifact,
                top_k=5,
                max_chars=6000,
            )
        )
        assembled_context = self.context_assembler.assemble(
            project=project,
            artifact_type=artifact_type,
            message=message,
            context_artifact=context_artifact,
            artifacts=artifacts,
            retrieval_result=retrieval_result,
        )

        stage_processor = processor_for_artifact(artifact_type)
        if stage_processor:
            processor_result = stage_processor.process(
                StageProcessorRequest(
                    project_id=project.id,
                    artifact_type=artifact_type.value,
                    stage_type=artifact_type.value,
                    project_snapshot=assembled_context["project_snapshot"],
                    input_artifacts=assembled_context["artifact_summaries"],
                    context_readiness=assembled_context["context_readiness"],
                    retrieval_result=retrieval_result.to_dict(),
                    prompt_version=intent.prompt_version,
                    metadata={"message": message, "intent_type": intent.intent_type},
                )
            )
            processor_result.warnings = [*processor_result.warnings, *retrieval_result.warnings]
            processor_result.metadata = {
                **processor_result.metadata,
                **self.action_builder.processor_metadata(
                    project=project,
                    intent=intent,
                    artifact_type=artifact_type,
                    retrieval=retrieval_result.to_dict(),
                    evidence=processor_result.evidence,
                    assumptions=processor_result.assumptions,
                    open_questions=processor_result.open_questions,
                    token_budget=assembled_context["token_budget"],
                    data_policy=assembled_context["data_policy"],
                ),
            }
            return processor_result

        return self.response_builder.unsupported_processor_response(
            artifact_type=artifact_type,
            evidence=assembled_context["evidence"],
            assumptions=assembled_context["assumptions"],
            open_questions=assembled_context["open_questions"],
            source_trace=retrieval_result.source_trace,
            warnings=retrieval_result.warnings,
            metadata=self.action_builder.processor_metadata(
                project=project,
                intent=intent,
                artifact_type=artifact_type,
                retrieval=retrieval_result.to_dict(),
                evidence=assembled_context["evidence"],
                assumptions=assembled_context["assumptions"],
                open_questions=assembled_context["open_questions"],
                token_budget=assembled_context["token_budget"],
                data_policy=assembled_context["data_policy"],
            ),
        )

    def _clean_message(self, message: str) -> str:
        text = (message or "").strip()
        if text.startswith("@"):
            parts = text.split(maxsplit=1)
            text = parts[1].strip() if len(parts) > 1 else ""
        for prefix in ("Сформулируй проблему:", "Проблема:", "problem:", "Goal:", "Цель:"):
            if text.lower().startswith(prefix.lower()):
                return text[len(prefix) :].strip()
        return text

    def _retrieval_query(self, message: str, artifact_type: ArtifactType) -> str:
        clean = self._clean_message(message)
        stage_terms = {
            ArtifactType.PROBLEM: "процессы боли ограничения причины симптомы участники",
            ArtifactType.GOAL: "цель KPI результат ограничения эффект",
            ArtifactType.BUSINESS_EFFECT: "эффект FTE стоимость риск метрики доход качество",
            ArtifactType.USE_CASES: "сценарии пользователи роли исключения требования",
            ArtifactType.FUNCTIONAL_REQUIREMENTS: "требования системы роли правила интеграции данные",
            ArtifactType.VALIDATION_REPORT: "качество validation readiness blockers warnings evidence completeness",
            ArtifactType.CONTEXT: "контекст источники readiness coverage gaps",
        }
        return f"{clean} {stage_terms.get(artifact_type, '')}".strip()
