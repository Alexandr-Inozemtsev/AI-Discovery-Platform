from typing import Any

from app.agents.runtime import StageProcessorRequest, StageProcessorResult
from app.models.discovery import ArtifactType
from app.processors.stage_draft_processor import clean_stage_text, evidence_from_request, result_from_patch, source_trace_from_request


PROMPT_VERSIONS = {
    ArtifactType.FUNCTIONAL_REQUIREMENTS.value: "functional_requirements.v1",
    ArtifactType.NON_FUNCTIONAL_REQUIREMENTS.value: "non_functional_requirements.v1",
    ArtifactType.FINAL_BT.value: "final_bt.v1",
}


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

        evidence = evidence_from_request(request)
        source_trace = source_trace_from_request(request)
        assumptions, open_questions, warnings = _grounding_state(request, evidence)
        prompt_version = request.prompt_version or PROMPT_VERSIONS[request.artifact_type]

        if request.artifact_type == ArtifactType.FUNCTIONAL_REQUIREMENTS.value:
            patch = _functional_requirements_patch(request, evidence, open_questions)
        elif request.artifact_type == ArtifactType.NON_FUNCTIONAL_REQUIREMENTS.value:
            patch = _non_functional_requirements_patch(request, evidence)
        else:
            patch = _final_bt_patch(request, evidence, assumptions, open_questions)

        patch.update({"evidence": evidence, "assumptions": assumptions, "open_questions": open_questions})
        return result_from_patch(
            request.artifact_type,
            patch,
            source_trace,
            warnings=warnings,
            prompt_version=prompt_version,
            used_fallback=True,
            used_inputs={
                "project_snapshot": bool(request.project_snapshot),
                "input_artifacts": True,
                "context_readiness": True,
                "retrieval_result": request.retrieval_result is not None,
                "user_answers": True,
            },
        )


def _functional_requirements_patch(
    request: StageProcessorRequest,
    evidence: list[dict[str, Any]],
    open_questions: list[str],
) -> dict[str, Any]:
    text = clean_stage_text(str(request.metadata.get("message") or ""))
    linked_use_case = _first_use_case_id(request.input_artifacts)
    existing_id = _stable_requirement_id(request.input_artifacts, ArtifactType.FUNCTIONAL_REQUIREMENTS.value, text, linked_use_case, "FR")
    has_basis = bool(evidence or linked_use_case or _artifact_has_content(request.input_artifacts, ArtifactType.PROBLEM.value) or _artifact_has_content(request.input_artifacts, ArtifactType.GOAL.value))
    if not has_basis:
        return {"functional_requirements": []}

    requirement = {
        "id": existing_id,
        "text": text,
        "priority": "MUST",
        "linked_use_case": linked_use_case,
        "acceptance_criteria": [_acceptance_criteria(text, linked_use_case)],
        "business_rules": ["Требование должно быть связано с подтверждённой проблемой, целью или use case."],
        "evidence": evidence,
        "assumption": not bool(evidence),
        "open_questions": open_questions,
    }
    return {"functional_requirements": [requirement]}


def _non_functional_requirements_patch(request: StageProcessorRequest, evidence: list[dict[str, Any]]) -> dict[str, Any]:
    text = clean_stage_text(str(request.metadata.get("message") or ""))
    category = _nfr_category(text)
    existing_id = _stable_requirement_id(request.input_artifacts, ArtifactType.NON_FUNCTIONAL_REQUIREMENTS.value, text, None, "NFR")
    has_basis = bool(evidence or _artifact_has_content(request.input_artifacts, ArtifactType.PROBLEM.value) or _artifact_has_content(request.input_artifacts, ArtifactType.GOAL.value) or _first_use_case_id(request.input_artifacts))
    if not has_basis:
        return {"non_functional_requirements": []}

    requirement = {
        "id": existing_id,
        "category": category,
        "text": text,
        "target_value": _target_value(text, category),
        "measurement": _measurement_for_category(category),
        "evidence": evidence,
        "assumption": not bool(evidence),
    }
    return {"non_functional_requirements": [requirement]}


def _final_bt_patch(
    request: StageProcessorRequest,
    evidence: list[dict[str, Any]],
    assumptions: list[str],
    open_questions: list[str],
) -> dict[str, Any]:
    validation = _structured(request.input_artifacts.get(ArtifactType.VALIDATION_REPORT.value))
    unresolved_questions = [*open_questions, *_collect_open_questions(request.input_artifacts)]
    sections = [
        {"id": "context", "title": "Контекст", "content": _artifact_content(request.input_artifacts, ArtifactType.CONTEXT.value)},
        {"id": "problem", "title": "Проблема", "content": _artifact_content(request.input_artifacts, ArtifactType.PROBLEM.value)},
        {"id": "goal", "title": "Цель", "content": _artifact_content(request.input_artifacts, ArtifactType.GOAL.value)},
        {"id": "business_effect", "title": "Бизнес-эффект", "content": _artifact_content(request.input_artifacts, ArtifactType.BUSINESS_EFFECT.value)},
        {"id": "use_cases", "title": "Use Cases", "content": _artifact_content(request.input_artifacts, ArtifactType.USE_CASES.value)},
        {"id": "requirements", "title": "Требования", "content": _requirements_content(request.input_artifacts)},
    ]
    return {
        "sections": sections,
        "validation_summary": {
            "warnings": validation.get("warnings") or [],
            "blockers": validation.get("blockers") or [],
            "validation_status": validation.get("validation_status") or ("requires_attention" if validation else "not_checked"),
        },
        "unresolved_questions": _unique_strings(unresolved_questions),
        "assumptions": assumptions,
        "evidence_summary": [
            {
                "source_id": row.get("source_id"),
                "chunk_id": row.get("chunk_id"),
                "source_name": row.get("source_name"),
            }
            for row in evidence
        ],
    }


def _grounding_state(
    request: StageProcessorRequest,
    evidence: list[dict[str, Any]],
) -> tuple[list[str], list[str], list[str]]:
    if evidence:
        return [], [], []
    if request.artifact_type == ArtifactType.FINAL_BT.value:
        return (
            ["Финальный документ собран без новых retrieved chunks; проверьте полноту source_trace."],
            ["Проверьте unresolved questions перед экспортом финального БТ."],
            ["Недостаточно evidence для полной проверки финального БТ."],
        )
    return (
        ["Требование сформировано без подтверждённых retrieved chunks и требует проверки."],
        ["Добавьте evidence или подтвердите требование с владельцем процесса."],
        ["Недостаточно evidence; requirement помечен как assumption."],
    )


def _first_use_case_id(input_artifacts: dict[str, Any]) -> str | None:
    use_cases = _structured(input_artifacts.get(ArtifactType.USE_CASES.value)).get("use_cases") or []
    if use_cases and isinstance(use_cases[0], dict):
        return use_cases[0].get("id") or None
    return None


def _stable_requirement_id(
    input_artifacts: dict[str, Any],
    artifact_type: str,
    text: str,
    linked_use_case: str | None,
    prefix: str,
) -> str:
    rows_key = "functional_requirements" if prefix == "FR" else "non_functional_requirements"
    rows = _structured(input_artifacts.get(artifact_type)).get(rows_key) or []
    normalized_text = text.lower().strip()
    for row in rows:
        if not isinstance(row, dict):
            continue
        row_text = str(row.get("text") or row.get("title") or row.get("description") or row.get("target") or "").lower().strip()
        if row_text == normalized_text or (linked_use_case and row.get("linked_use_case") == linked_use_case):
            return row.get("id") or f"{prefix}-001"
    return f"{prefix}-001"


def _acceptance_criteria(text: str, linked_use_case: str | None) -> str:
    if "договор" in text.lower():
        return "Результат автоматической проверки договора доступен пользователю процесса."
    if linked_use_case:
        return f"Сценарий {linked_use_case} выполняется с учётом требования."
    return "Результат выполнения требования подтверждён владельцем процесса."


def _nfr_category(text: str) -> str:
    lower = text.lower()
    if any(word in lower for word in ("сек", "мс", "время", "производ", "latency", "response")):
        return "performance"
    if any(word in lower for word in ("роль", "доступ", "шифр", "security", "авторизац")):
        return "security"
    if any(word in lower for word in ("аудит", "лог", "журнал")):
        return "audit"
    if any(word in lower for word in ("доступность", "uptime", "sla")):
        return "availability"
    if any(word in lower for word in ("ux", "удоб", "usability")):
        return "usability"
    if any(word in lower for word in ("интеграц", "api", "очеред")):
        return "integration"
    return "data"


def _target_value(text: str, category: str) -> str:
    lower = text.lower()
    marker = "до "
    if marker in lower:
        return text[lower.index(marker) :].strip()
    if category == "performance":
        return "Требует уточнения целевого времени отклика."
    return "Требует уточнения целевого значения."


def _measurement_for_category(category: str) -> str:
    return {
        "performance": "Замерить p95/p99 время ответа на тестовом и продуктивном контуре.",
        "security": "Проверить матрицу доступа и результаты security review.",
        "audit": "Проверить наличие audit trail и полноту событий.",
        "availability": "Сравнить фактический uptime с SLA.",
        "usability": "Провести UX-проверку с пользователями процесса.",
        "integration": "Проверить контракт интеграции и обработку ошибок.",
        "data": "Проверить качество, полноту и актуальность данных.",
    }[category]


def _artifact_has_content(input_artifacts: dict[str, Any], artifact_type: str) -> bool:
    artifact = input_artifacts.get(artifact_type) or {}
    if not isinstance(artifact, dict):
        return False
    return bool(artifact.get("content") or _structured(artifact))


def _artifact_content(input_artifacts: dict[str, Any], artifact_type: str) -> str:
    artifact = input_artifacts.get(artifact_type) or {}
    if not isinstance(artifact, dict):
        return ""
    if artifact.get("content"):
        return str(artifact.get("content"))
    structured = _structured(artifact)
    if artifact_type == ArtifactType.PROBLEM.value:
        return str(structured.get("problem_statement") or "")
    if artifact_type == ArtifactType.GOAL.value:
        return str(structured.get("desired_outcome") or structured.get("recommended_goal") or "")
    return ""


def _requirements_content(input_artifacts: dict[str, Any]) -> str:
    parts = []
    for artifact_type, key in (
        (ArtifactType.FUNCTIONAL_REQUIREMENTS.value, "functional_requirements"),
        (ArtifactType.NON_FUNCTIONAL_REQUIREMENTS.value, "non_functional_requirements"),
    ):
        artifact = input_artifacts.get(artifact_type) or {}
        if isinstance(artifact, dict) and artifact.get("content"):
            parts.append(str(artifact.get("content")))
        rows = _structured(artifact).get(key) or []
        for row in rows:
            if isinstance(row, dict):
                parts.append(f"{row.get('id', '')} {row.get('text') or row.get('title') or ''}".strip())
    return "\n".join(part for part in parts if part)


def _collect_open_questions(input_artifacts: dict[str, Any]) -> list[str]:
    questions = []
    for artifact in input_artifacts.values():
        structured = _structured(artifact)
        for question in structured.get("open_questions") or []:
            if isinstance(question, str):
                questions.append(question)
    return questions


def _structured(artifact: Any) -> dict[str, Any]:
    if isinstance(artifact, dict):
        value = artifact.get("structured_content")
        if isinstance(value, dict):
            return value
        if any(key in artifact for key in ("use_cases", "functional_requirements", "non_functional_requirements", "warnings", "blockers")):
            return artifact
    return {}


def _unique_strings(values: list[str]) -> list[str]:
    result = []
    seen = set()
    for value in values:
        text = str(value or "").strip()
        if text and text not in seen:
            result.append(text)
            seen.add(text)
    return result
