from typing import Any

from app.agents.runtime import StageProcessorRequest, StageProcessorResult
from app.models.discovery import ArtifactType


GROUNDING_FIELDS = {"evidence", "assumptions", "open_questions", "source_trace"}


class StageDraftProcessor:
    supported_artifact_types = {
        ArtifactType.PROBLEM.value,
        ArtifactType.GOAL.value,
        ArtifactType.BUSINESS_EFFECT.value,
        ArtifactType.USE_CASES.value,
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

        if request.artifact_type == ArtifactType.PROBLEM.value:
            patch = {
                "problem_statement": text,
                "pains": [first_evidence_text(evidence) or text],
                "root_causes": ["Ручной или неавтоматизированный процесс требует проверки на источниках."],
                "questions": open_questions,
            }
        elif request.artifact_type == ArtifactType.GOAL.value:
            patch = {
                "recommended_goal": text,
                "smart": {
                    "specific": text,
                    "measurable": "Метрика требует подтверждения источниками.",
                    "achievable": "Достижимость нужно проверить с владельцами процесса.",
                    "relevant": "Цель связана с заявленным Discovery контекстом.",
                    "time_bound": "Срок требует уточнения.",
                },
                "kpi": [{"name": "Сокращение ручных операций", "target": "Требует подтверждения", "unit": "%"}],
                "assumptions": assumptions,
            }
        elif request.artifact_type == ArtifactType.BUSINESS_EFFECT.value:
            patch = {
                "qualitative_effect": [text],
                "quantitative_effect": [{"metric": "Экономия времени", "value": "Требует расчёта", "confidence": "assumption"}],
                "metrics": [{"name": "Повторные визиты", "direction": "decrease", "evidence_required": True}],
                "open_questions": open_questions,
            }
        else:
            patch = {
                "use_cases": [
                    {
                        "title": text,
                        "actor": "Пользователь процесса",
                        "flow": ["Открыть задачу", "Проверить данные", "Подтвердить результат"],
                        "exceptions": ["Нет данных в источниках", "Требуется ручное подтверждение"],
                        "linked_requirements": ["FR-001"],
                    }
                ]
            }

        patch.update({"evidence": evidence, "assumptions": assumptions, "open_questions": open_questions})
        return result_from_patch(request.artifact_type, patch, source_trace)


def result_from_patch(artifact_type: str, patch: dict[str, Any], source_trace: list[dict[str, Any]]) -> StageProcessorResult:
    changed_fields = [key for key in patch.keys() if key not in GROUNDING_FIELDS]
    return StageProcessorResult(
        ok=True,
        artifact_type=artifact_type,
        content=content_from_patch(artifact_type, patch),
        structured_content=patch,
        proposed_patch=patch,
        preview={
            "target_artifact_type": artifact_type,
            "changed_fields": changed_fields,
            "summary": f"Будут изменены поля: {', '.join(changed_fields)}.",
            "evidence_count": len(patch.get("evidence") or []),
            "warnings": [],
        },
        evidence=patch.get("evidence") or [],
        assumptions=patch.get("assumptions") or [],
        open_questions=patch.get("open_questions") or [],
        source_trace=source_trace,
        human_message="Я подготовил черновик изменения. Проверьте preview перед применением.",
        metadata={"processor": "stage_draft_processor"},
    )


def clean_stage_text(message: str) -> str:
    text = (message or "").strip()
    if text.startswith("@"):
        parts = text.split(maxsplit=1)
        text = parts[1].strip() if len(parts) > 1 else ""
    prefixes = (
        "Сформулируй проблему:",
        "Проблема:",
        "problem:",
        "Goal:",
        "Цель:",
        "Эффект:",
        "Сценарий:",
        "Требование:",
        "НФТ:",
        "Финальный БТ:",
    )
    for prefix in prefixes:
        if text.lower().startswith(prefix.lower()):
            return text[len(prefix) :].strip()
    return text


def evidence_from_request(request: StageProcessorRequest) -> list[dict[str, Any]]:
    retrieval = request.retrieval_result or {}
    chunks = retrieval.get("chunks") if isinstance(retrieval, dict) else []
    evidence = []
    for chunk in chunks or []:
        if not isinstance(chunk, dict):
            continue
        evidence.append(
            {
                "source_id": chunk.get("source_id"),
                "chunk_id": chunk.get("chunk_id") or chunk.get("id"),
                "source_name": chunk.get("source_name") or chunk.get("name"),
                "text": chunk.get("text"),
            }
        )
    return evidence


def source_trace_from_request(request: StageProcessorRequest) -> list[dict[str, Any]]:
    retrieval = request.retrieval_result or {}
    if not isinstance(retrieval, dict):
        return []
    source_trace = retrieval.get("source_trace")
    return source_trace if isinstance(source_trace, list) else []


def grounding_notes(evidence: list[dict[str, Any]]) -> tuple[list[str], list[str]]:
    if evidence:
        return [], []
    return (
        ["Вывод сформирован без подтверждённых retrieved chunks и требует проверки."],
        ["Добавьте evidence или подтвердите вывод с владельцем процесса."],
    )


def first_evidence_text(evidence: list[dict[str, Any]]) -> str:
    for row in evidence:
        text = str(row.get("text") or "").strip()
        if text:
            return text
    return ""


def content_from_patch(artifact_type: str, patch: dict[str, Any]) -> str:
    if artifact_type == ArtifactType.PROBLEM.value:
        return str(patch.get("problem_statement") or "")
    if artifact_type == ArtifactType.GOAL.value:
        return str(patch.get("recommended_goal") or "")
    if artifact_type == ArtifactType.BUSINESS_EFFECT.value:
        return "; ".join(str(item) for item in patch.get("qualitative_effect") or [])
    if artifact_type == ArtifactType.USE_CASES.value:
        use_cases = patch.get("use_cases") or []
        return str(use_cases[0].get("title") if use_cases else "")
    if artifact_type == ArtifactType.FUNCTIONAL_REQUIREMENTS.value:
        rows = patch.get("functional_requirements") or []
        return str(rows[0].get("title") if rows else "")
    if artifact_type == ArtifactType.NON_FUNCTIONAL_REQUIREMENTS.value:
        rows = patch.get("non_functional_requirements") or []
        return str(rows[0].get("target") if rows else "")
    if artifact_type == ArtifactType.FINAL_BT.value:
        return str((patch.get("document_preview") or {}).get("title") or "")
    return str(patch.get("content") or "")
