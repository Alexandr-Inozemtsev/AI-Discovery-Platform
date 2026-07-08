from app.agents.runtime import StageProcessorResult
from app.models.discovery import ArtifactType


class AssistantResponseBuilder:
    def guidance_response(self, intent_type: str, confidence: float, artifact_type: ArtifactType | None = None) -> StageProcessorResult:
        return StageProcessorResult(
            ok=True,
            artifact_type=(artifact_type.value if artifact_type else ""),
            human_message="Я готов помочь пройти Discovery workflow. Уточните этап или артефакт, который нужно обновить.",
            metadata={"intent_type": intent_type, "confidence": confidence},
        )

    def policy_denied_response(self, artifact_type: ArtifactType, intent_type: str, action_name: str) -> StageProcessorResult:
        return StageProcessorResult(
            ok=False,
            artifact_type=artifact_type.value,
            human_message="Действие запрещено политикой AI-чата.",
            errors=[f"Tool action is not allowed: {action_name}"],
            metadata={"intent_type": intent_type},
        )

    def unsupported_processor_response(
        self,
        *,
        artifact_type: ArtifactType,
        evidence: list,
        assumptions: list,
        open_questions: list,
        source_trace: list,
        warnings: list,
        metadata: dict,
    ) -> StageProcessorResult:
        return StageProcessorResult(
            ok=True,
            artifact_type=artifact_type.value,
            content="",
            structured_content={},
            proposed_patch={},
            preview={},
            evidence=evidence,
            assumptions=list(assumptions),
            open_questions=list(open_questions),
            source_trace=source_trace,
            warnings=warnings,
            human_message="Для этого этапа AI Chat пока не формирует patch. Я могу показать состояние или предложить уточняющие вопросы.",
            metadata=metadata,
        )
