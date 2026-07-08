from app.assistant.chat_context_assembler import ChatContextAssembler
from app.assistant.intent_router import IntentRouter, RoutedIntent
from app.assistant.processors import processor_for_artifact
from app.agents.runtime import StageProcessorResult, ToolAction, ToolPolicy
from app.agents.runtime.stage_processor_contract import StageProcessorRequest
from app.models.discovery import ArtifactType, DiscoveryProject
from app.rag.simple_retriever import RetrievalQuery, SimpleRetriever


class DiscoveryChatOrchestrator:
    def __init__(
        self,
        intent_router: IntentRouter | None = None,
        tool_policy: ToolPolicy | None = None,
        retriever: SimpleRetriever | None = None,
        context_assembler: ChatContextAssembler | None = None,
    ):
        self.intent_router = intent_router or IntentRouter()
        self.tool_policy = tool_policy or ToolPolicy.for_ai_discovery_chat()
        self.retriever = retriever or SimpleRetriever()
        self.context_assembler = context_assembler or ChatContextAssembler()

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
        if intent.intent_type == "draft_artifact_patch" and intent.target_artifact_type:
            result = self._draft_patch(project, message, intent, context_artifact or {}, artifacts or {})
        else:
            result = StageProcessorResult(
                ok=True,
                artifact_type=(intent.target_artifact_type.value if intent.target_artifact_type else ""),
                human_message="Я готов помочь пройти Discovery workflow. Уточните этап или артефакт, который нужно обновить.",
                metadata={"intent_type": intent.intent_type, "confidence": intent.confidence},
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
                return StageProcessorResult(
                    ok=False,
                    artifact_type=artifact_type.value,
                    human_message="Действие запрещено политикой AI-чата.",
                    errors=[f"Tool action is not allowed: {action_name}"],
                    metadata={"intent_type": intent.intent_type},
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

        evidence = assembled_context["evidence"]
        assumptions = list(assembled_context["assumptions"])
        open_questions = list(assembled_context["open_questions"])
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
                "intent_type": intent.intent_type,
                "confidence": intent.confidence,
                "command": intent.command,
                "prompt_version": intent.prompt_version,
                "prompt_instruction": intent.instruction,
                "project_id": project.id,
                "source": "ai_discovery_chat",
                "retrieval": retrieval_result.to_dict(),
                "evidence": processor_result.evidence,
                "assumptions": processor_result.assumptions,
                "open_questions": processor_result.open_questions,
                "token_budget": assembled_context["token_budget"],
                "data_policy": assembled_context["data_policy"],
            }
            return processor_result

        proposed_patch = self._build_proposed_patch(artifact_type, message, evidence, assumptions, open_questions)
        changed_fields = [field for field in proposed_patch.keys() if field not in {"evidence", "assumptions", "open_questions"}]
        preview = {"target_artifact_type": artifact_type.value, "changed_fields": changed_fields, "summary": f"Будут изменены поля: {', '.join(changed_fields)}.", "evidence_count": len(evidence), "warnings": retrieval_result.warnings}
        return StageProcessorResult(
            ok=True,
            artifact_type=artifact_type.value,
            content=self._content_from_patch(artifact_type, proposed_patch),
            structured_content=proposed_patch,
            proposed_patch=proposed_patch,
            preview=preview,
            evidence=evidence,
            assumptions=assumptions,
            open_questions=open_questions,
            source_trace=retrieval_result.source_trace,
            warnings=retrieval_result.warnings,
            human_message="Я подготовил черновик изменения. Проверьте preview перед применением.",
            metadata={
                "intent_type": intent.intent_type,
                "confidence": intent.confidence,
                "command": intent.command,
                "prompt_version": intent.prompt_version,
                "prompt_instruction": intent.instruction,
                "project_id": project.id,
                "source": "ai_discovery_chat",
                "retrieval": retrieval_result.to_dict(),
                "evidence": evidence,
                "assumptions": assumptions,
                "open_questions": open_questions,
                "token_budget": assembled_context["token_budget"],
                "data_policy": assembled_context["data_policy"],
            },
        )

    def _build_proposed_patch(
        self,
        artifact_type: ArtifactType,
        message: str,
        evidence: list[dict],
        assumptions: list[str],
        open_questions: list[str],
    ) -> dict:
        clean_message = self._clean_message(message)
        grounding = {
            "evidence": evidence,
            "assumptions": assumptions,
            "open_questions": open_questions,
        }
        if artifact_type == ArtifactType.PROBLEM:
            return {"problem_statement": clean_message, **grounding}
        if artifact_type == ArtifactType.GOAL:
            return {"desired_outcome": clean_message, **grounding}
        return {"content": clean_message, **grounding}

    def _content_from_patch(self, artifact_type: ArtifactType, proposed_patch: dict) -> str:
        if artifact_type == ArtifactType.PROBLEM:
            return str(proposed_patch.get("problem_statement") or "")
        if artifact_type == ArtifactType.GOAL:
            return str(proposed_patch.get("desired_outcome") or "")
        return str(proposed_patch.get("content") or "")

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
            ArtifactType.CONTEXT: "контекст источники readiness coverage gaps",
        }
        return f"{clean} {stage_terms.get(artifact_type, '')}".strip()
