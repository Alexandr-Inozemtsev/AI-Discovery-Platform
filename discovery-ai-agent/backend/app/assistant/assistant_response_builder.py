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

    def answer_from_context_response(
        self,
        *,
        intent_type: str,
        query: str,
        evidence: list[dict],
        source_trace: list[dict],
        warnings: list[str],
        metadata: dict,
    ) -> StageProcessorResult:
        if evidence:
            snippets = []
            for item in evidence[:3]:
                source_name = item.get("source_name") or item.get("source_id") or "источник"
                text = str(item.get("text") or "").strip()
                if len(text) > 700:
                    text = text[:686] + "...[truncated]"
                snippets.append(f"- {source_name}: {text}")
            human_message = "Нашёл подтверждение в загруженных источниках:\n" + "\n".join(snippets)
        else:
            human_message = "В загруженных источниках подтверждение не найдено. Попробуйте уточнить запрос или обновить контекст."

        return StageProcessorResult(
            ok=True,
            artifact_type="",
            content=human_message,
            structured_content={
                "answer": human_message,
                "query": query,
                "evidence_count": len(evidence),
            },
            proposed_patch={},
            preview={},
            evidence=evidence,
            source_trace=source_trace,
            warnings=warnings,
            human_message=human_message,
            metadata={**metadata, "intent_type": intent_type},
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
