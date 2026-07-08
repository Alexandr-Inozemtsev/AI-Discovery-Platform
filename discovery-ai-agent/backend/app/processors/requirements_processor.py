from app.agents.runtime import StageProcessorRequest, StageProcessorResult
from app.models.discovery import ArtifactType
from app.processors.stage_draft_processor import (
    clean_stage_text,
    evidence_from_request,
    grounding_notes,
    result_from_patch,
    source_trace_from_request,
)


class RequirementsProcessor:
    supported_artifact_types = {
        ArtifactType.FUNCTIONAL_REQUIREMENTS.value,
        ArtifactType.NON_FUNCTIONAL_REQUIREMENTS.value,
        ArtifactType.FINAL_BT.value,
    }

    def process(self, request: StageProcessorRequest) -> StageProcessorResult:
        if request.contains_secret_fields():
            return StageProcessorResult(
                ok=False,
                artifact_type=request.artifact_type,
                human_message="Запрос содержит поля, похожие на секреты. Уберите credentials и повторите запрос.",
                errors=["Secret-like fields are not allowed in StageProcessorRequest."],
            )
        if request.artifact_type not in self.supported_artifact_types:
            return StageProcessorResult(
                ok=False,
                artifact_type=request.artifact_type,
                human_message="Этот processor не поддерживает выбранный тип артефакта.",
                errors=[f"Unsupported artifact type: {request.artifact_type}"],
            )

        text = clean_stage_text(str(request.metadata.get("message") or ""))
        evidence = evidence_from_request(request)
        assumptions, open_questions = grounding_notes(evidence)
        source_trace = source_trace_from_request(request)

        if request.artifact_type == ArtifactType.FUNCTIONAL_REQUIREMENTS.value:
            patch = {
                "functional_requirements": [
                    {
                        "id": "FR-001",
                        "title": text,
                        "description": text,
                        "acceptance_criteria": ["Критерии приёмки требуют подтверждения владельцем процесса."],
                        "evidence": evidence,
                        "assumption": not bool(evidence),
                    }
                ]
            }
        elif request.artifact_type == ArtifactType.NON_FUNCTIONAL_REQUIREMENTS.value:
            patch = {
                "non_functional_requirements": [
                    {
                        "id": "NFR-001",
                        "quality_attribute": "Производительность",
                        "target": text,
                        "measurement": "Метод измерения требует уточнения.",
                        "assumption": not bool(evidence),
                    }
                ]
            }
        else:
            patch = {
                "document_preview": {
                    "title": text or "Финальный бизнес-требования документ",
                    "sections": ["Контекст", "Проблема", "Цель", "Бизнес-эффект", "Use Cases", "Требования"],
                },
                "validation_warnings": open_questions or ["Перед экспортом проверьте полноту evidence и unresolved assumptions."],
                "export": {"format": "docx", "ready": False},
            }

        patch.update({"evidence": evidence, "assumptions": assumptions, "open_questions": open_questions})
        return result_from_patch(request.artifact_type, patch, source_trace)
