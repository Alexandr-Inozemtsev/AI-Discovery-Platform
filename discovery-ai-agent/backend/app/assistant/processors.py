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

        text = _clean_stage_text(str(request.metadata.get("message") or ""))
        evidence = _evidence_from_request(request)
        assumptions, open_questions = _grounding_notes(evidence)
        source_trace = _source_trace_from_request(request)

        if request.artifact_type == ArtifactType.PROBLEM.value:
            patch = {
                "problem_statement": text,
                "pains": [_first_evidence_text(evidence) or text],
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
        return _result_from_patch(request.artifact_type, patch, source_trace)


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

        text = _clean_stage_text(str(request.metadata.get("message") or ""))
        evidence = _evidence_from_request(request)
        assumptions, open_questions = _grounding_notes(evidence)
        source_trace = _source_trace_from_request(request)

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
        return _result_from_patch(request.artifact_type, patch, source_trace)


class ValidationProcessor:
    supported_artifact_types = {ArtifactType.VALIDATION_REPORT.value}

    def process(self, request: StageProcessorRequest) -> StageProcessorResult:
        if request.contains_secret_fields():
            return StageProcessorResult(
                ok=False,
                artifact_type=request.artifact_type,
                human_message="Запрос содержит поля, похожие на секреты. Уберите credentials и повторите запрос.",
                errors=["Secret-like fields are not allowed in StageProcessorRequest."],
            )

        artifacts = request.input_artifacts or {}
        warnings = []
        blockers = []
        required = (ArtifactType.PROBLEM.value, ArtifactType.GOAL.value, ArtifactType.FUNCTIONAL_REQUIREMENTS.value)
        for artifact_type in required:
            artifact = artifacts.get(artifact_type) or {}
            structured_keys = artifact.get("structured_keys") if isinstance(artifact, dict) else []
            if not structured_keys:
                blockers.append(f"Артефакт {artifact_type} не содержит структурированных полей.")
        if not artifacts:
            warnings.append("Нет артефактов для проверки качества Discovery workflow.")

        report = {
            "validation_status": "requires_attention" if blockers or warnings else "ready",
            "warnings": warnings or ["Проверьте evidence, assumptions и открытые вопросы перед экспортом."],
            "blockers": blockers,
            "checked_artifacts": sorted(artifacts.keys()),
            "quality_gates": {
                "has_problem": ArtifactType.PROBLEM.value in artifacts,
                "has_goal": ArtifactType.GOAL.value in artifacts,
                "has_requirements": ArtifactType.FUNCTIONAL_REQUIREMENTS.value in artifacts,
            },
        }
        return StageProcessorResult(
            ok=True,
            artifact_type=ArtifactType.VALIDATION_REPORT.value,
            content="Проверка качества Discovery workflow выполнена.",
            structured_content=report,
            proposed_patch={},
            preview={},
            warnings=report["warnings"],
            errors=blockers,
            human_message="Я проверил качество Discovery workflow. Изменения в артефакты не применялись.",
            metadata={"processor": "assistant_validation_processor"},
        )


def processor_for_artifact(artifact_type: ArtifactType | str) -> StageDraftProcessor | RequirementsProcessor | ValidationProcessor | None:
    value = artifact_type.value if isinstance(artifact_type, ArtifactType) else str(artifact_type)
    if value in StageDraftProcessor.supported_artifact_types:
        return StageDraftProcessor()
    if value in RequirementsProcessor.supported_artifact_types:
        return RequirementsProcessor()
    if value in ValidationProcessor.supported_artifact_types:
        return ValidationProcessor()
    return None


def _result_from_patch(artifact_type: str, patch: dict[str, Any], source_trace: list[dict[str, Any]]) -> StageProcessorResult:
    changed_fields = [key for key in patch.keys() if key not in GROUNDING_FIELDS]
    return StageProcessorResult(
        ok=True,
        artifact_type=artifact_type,
        content=_content_from_patch(artifact_type, patch),
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
        metadata={"processor": "assistant_stage_processor"},
    )


def _clean_stage_text(message: str) -> str:
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


def _evidence_from_request(request: StageProcessorRequest) -> list[dict[str, Any]]:
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


def _source_trace_from_request(request: StageProcessorRequest) -> list[dict[str, Any]]:
    retrieval = request.retrieval_result or {}
    if not isinstance(retrieval, dict):
        return []
    source_trace = retrieval.get("source_trace")
    return source_trace if isinstance(source_trace, list) else []


def _grounding_notes(evidence: list[dict[str, Any]]) -> tuple[list[str], list[str]]:
    if evidence:
        return [], []
    return (
        ["Вывод сформирован без подтверждённых retrieved chunks и требует проверки."],
        ["Добавьте evidence или подтвердите вывод с владельцем процесса."],
    )


def _first_evidence_text(evidence: list[dict[str, Any]]) -> str:
    for row in evidence:
        text = str(row.get("text") or "").strip()
        if text:
            return text
    return ""


def _content_from_patch(artifact_type: str, patch: dict[str, Any]) -> str:
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
