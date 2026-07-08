from typing import Any

from app.agents.runtime import StageProcessorRequest, StageProcessorResult
from app.models.discovery import ArtifactType


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
        checks: list[dict[str, Any]] = []
        if not artifacts:
            checks.append(_check("VAL-000", "WORKFLOW", "blocker", "Discovery workflow пустой.", "Заполните Context, Problem, Goal и Requirements перед проверкой качества.", ArtifactType.VALIDATION_REPORT.value))
        _check_context(artifacts, checks)
        _check_problem(artifacts, checks)
        _check_goal(artifacts, checks)
        _check_business_effect(artifacts, checks)
        _check_use_cases(artifacts, checks)
        _check_requirements(artifacts, checks)
        _check_final_bt(artifacts, checks)

        blockers = [check["message"] for check in checks if check["severity"] == "blocker"]
        errors = [check["message"] for check in checks if check["severity"] == "error"]
        warnings = [check["message"] for check in checks if check["severity"] == "warning"]
        if blockers or errors:
            overall_status = "blocked"
        elif warnings:
            overall_status = "warning"
        else:
            overall_status = "ready"

        score = _score(checks)
        report = {
            "overall_status": overall_status,
            "score": score,
            "checks": checks,
            "blockers": blockers,
            "warnings": warnings,
            "next_actions": _next_actions(checks),
        }
        return StageProcessorResult(
            ok=True,
            artifact_type=ArtifactType.VALIDATION_REPORT.value,
            content="Проверка качества Discovery workflow выполнена.",
            structured_content=report,
            proposed_patch=report,
            preview={
                "target_artifact_type": ArtifactType.VALIDATION_REPORT.value,
                "changed_fields": ["overall_status", "score", "checks", "blockers", "warnings", "next_actions"],
                "summary": "Будет сохранён отчёт проверки качества Discovery workflow.",
                "warnings": warnings,
            },
            warnings=warnings,
            errors=[*blockers, *errors],
            human_message="Я проверил качество Discovery workflow и подготовил validation report.",
            metadata={"processor": "validation_processor", "prompt_version": request.prompt_version or "validation_report.v1"},
        )


def _check_context(artifacts: dict[str, Any], checks: list[dict[str, Any]]) -> None:
    artifact = artifacts.get(ArtifactType.CONTEXT.value)
    structured = _structured(artifact)
    if not artifact:
        checks.append(_check("VAL-001", "CONTEXT", "warning", "Контекст не заполнен.", "Добавьте источники, readiness, coverage и source_trace.", ArtifactType.CONTEXT.value))
        return
    if not _has_any(structured, "readiness") and not _has_key_summary(artifact, "readiness"):
        checks.append(_check("VAL-002", "CONTEXT", "warning", "В контексте нет readiness.", "Запустите анализ контекста или заполните readiness вручную.", ArtifactType.CONTEXT.value))
    if not _has_any(structured, "coverage") and not _has_key_summary(artifact, "coverage"):
        checks.append(_check("VAL-003", "CONTEXT", "warning", "В контексте нет coverage.", "Проверьте покрытие источников по ключевым вопросам.", ArtifactType.CONTEXT.value))
    if not _has_any(structured, "source_trace") and not _has_key_summary(artifact, "source_trace"):
        checks.append(_check("VAL-004", "CONTEXT", "warning", "В контексте нет source_trace.", "Сохраните трассировку источников для evidence.", ArtifactType.CONTEXT.value))
    for source in [*(structured.get("documents") or []), *(structured.get("uploaded_files") or []), *(structured.get("links") or [])]:
        if isinstance(source, dict) and (source.get("content_level") == "metadata_only" or source.get("text_extraction_status") == "not_available"):
            checks.append(_check("VAL-005", "CONTEXT", "warning", "Есть metadata_only источник без usable evidence.", "Не используйте metadata_only source как evidence.", ArtifactType.CONTEXT.value))


def _check_problem(artifacts: dict[str, Any], checks: list[dict[str, Any]]) -> None:
    artifact = artifacts.get(ArtifactType.PROBLEM.value)
    structured = _structured(artifact)
    if not artifact:
        checks.append(_check("VAL-010", "PROBLEM", "blocker", "Проблема не заполнена.", "Сформулируйте problem_statement.", ArtifactType.PROBLEM.value))
        return
    statement = str(structured.get("problem_statement") or _content(artifact) or "").strip()
    if not statement:
        checks.append(_check("VAL-011", "PROBLEM", "blocker", "Нет problem_statement.", "Сформулируйте проблему без описания решения.", ArtifactType.PROBLEM.value))
    if _contains_solution(statement):
        checks.append(_check("VAL-012", "PROBLEM", "warning", "Problem statement похож на описание решения.", "Переформулируйте проблему без solution wording.", ArtifactType.PROBLEM.value))
    if not (structured.get("user_pains") or structured.get("business_pains") or structured.get("pains")):
        checks.append(_check("VAL-013", "PROBLEM", "warning", "В проблеме не указаны pains.", "Добавьте пользовательские или бизнес-боли.", ArtifactType.PROBLEM.value))
    if not structured.get("root_causes"):
        checks.append(_check("VAL-014", "PROBLEM", "warning", "В проблеме не указаны root causes.", "Добавьте причины или отметьте их как open question.", ArtifactType.PROBLEM.value))
    if not (structured.get("evidence") or structured.get("assumptions")):
        checks.append(_check("VAL-015", "PROBLEM", "warning", "Проблема не имеет evidence или assumptions.", "Добавьте evidence или явно отметьте assumption.", ArtifactType.PROBLEM.value))


def _check_goal(artifacts: dict[str, Any], checks: list[dict[str, Any]]) -> None:
    artifact = artifacts.get(ArtifactType.GOAL.value)
    structured = _structured(artifact)
    if not artifact:
        checks.append(_check("VAL-020", "GOAL", "blocker", "Цель не заполнена.", "Сформулируйте цель и SMART.", ArtifactType.GOAL.value))
        return
    if not (structured.get("smart_analysis") or structured.get("smart")):
        checks.append(_check("VAL-021", "GOAL", "warning", "Цель не проверена по SMART.", "Добавьте SMART analysis.", ArtifactType.GOAL.value))
    if not (structured.get("success_metrics") or structured.get("kpi") or structured.get("open_questions")):
        checks.append(_check("VAL-022", "GOAL", "warning", "У цели нет KPI или open_questions.", "Добавьте KPI либо явно зафиксируйте open_questions по метрикам.", ArtifactType.GOAL.value))
    if not artifacts.get(ArtifactType.PROBLEM.value):
        checks.append(_check("VAL-023", "GOAL", "error", "Цель не связана с Problem.", "Сначала заполните Problem или добавьте связь цели с проблемой.", ArtifactType.GOAL.value))


def _check_business_effect(artifacts: dict[str, Any], checks: list[dict[str, Any]]) -> None:
    artifact = artifacts.get(ArtifactType.BUSINESS_EFFECT.value)
    structured = _structured(artifact)
    if not artifact:
        checks.append(_check("VAL-030", "BUSINESS_EFFECT", "warning", "Бизнес-эффект не заполнен.", "Добавьте qualitative effects и метрики.", ArtifactType.BUSINESS_EFFECT.value))
        return
    if not (structured.get("qualitative_effects") or structured.get("qualitative_effect")):
        checks.append(_check("VAL-031", "BUSINESS_EFFECT", "warning", "Нет qualitative effect.", "Опишите качественный бизнес-эффект.", ArtifactType.BUSINESS_EFFECT.value))
    for metric in structured.get("quantitative_metrics") or structured.get("quantitative_effect") or []:
        if isinstance(metric, dict) and metric.get("confidence") not in {"confirmed", "assumption"}:
            checks.append(_check("VAL-032", "BUSINESS_EFFECT", "warning", "Количественная метрика не помечена confirmed/assumption.", "Укажите confidence для quantitative metric.", ArtifactType.BUSINESS_EFFECT.value))
    if not (structured.get("measurement_method") or structured.get("open_questions")):
        checks.append(_check("VAL-033", "BUSINESS_EFFECT", "warning", "Нет measurement method или вопроса по измерению.", "Добавьте метод измерения эффекта или open question.", ArtifactType.BUSINESS_EFFECT.value))


def _check_use_cases(artifacts: dict[str, Any], checks: list[dict[str, Any]]) -> None:
    structured = _structured(artifacts.get(ArtifactType.USE_CASES.value))
    use_cases = structured.get("use_cases") or []
    if not use_cases:
        checks.append(_check("VAL-040", "USE_CASES", "warning", "Use cases не заполнены.", "Добавьте хотя бы один use case.", ArtifactType.USE_CASES.value))
        return
    for index, use_case in enumerate(use_cases, start=1):
        if not isinstance(use_case, dict):
            continue
        prefix = f"Use case {use_case.get('id') or index}"
        for field_name, message in (
            ("actor", "нет actor"),
            ("trigger", "нет trigger"),
            ("main_flow", "нет main flow"),
            ("exceptions", "нет exceptions"),
        ):
            if not use_case.get(field_name):
                checks.append(_check(f"VAL-04{index}", "USE_CASES", "warning", f"{prefix}: {message}.", "Заполните обязательные поля use case.", ArtifactType.USE_CASES.value))
        if not (use_case.get("linked_requirements") or use_case.get("requirements")):
            checks.append(_check(f"VAL-04{index}R", "USE_CASES", "warning", f"{prefix}: нет linked requirements.", "Свяжите use case с FR/NFR.", ArtifactType.USE_CASES.value))


def _check_requirements(artifacts: dict[str, Any], checks: list[dict[str, Any]]) -> None:
    rows = [
        *(_structured(artifacts.get(ArtifactType.FUNCTIONAL_REQUIREMENTS.value)).get("functional_requirements") or []),
        *(_structured(artifacts.get(ArtifactType.NON_FUNCTIONAL_REQUIREMENTS.value)).get("non_functional_requirements") or []),
    ]
    if not rows:
        checks.append(_check("VAL-050", "REQUIREMENTS", "warning", "Требования не заполнены.", "Добавьте FR/NFR перед Final BT.", ArtifactType.FUNCTIONAL_REQUIREMENTS.value))
        return
    seen = set()
    for row in rows:
        if not isinstance(row, dict):
            continue
        requirement_id = row.get("id")
        text = str(row.get("text") or row.get("title") or row.get("description") or "").strip()
        if not requirement_id:
            checks.append(_check("VAL-051", "REQUIREMENTS", "error", "У требования нет ID.", "Назначьте стабильный ID FR/NFR.", ArtifactType.FUNCTIONAL_REQUIREMENTS.value))
        if not text or len(text.split()) < 2:
            checks.append(_check("VAL-052", "REQUIREMENTS", "warning", f"Требование {requirement_id or ''} сформулировано неоднозначно.", "Уточните формулировку требования.", ArtifactType.FUNCTIONAL_REQUIREMENTS.value))
        if text.lower() in seen:
            checks.append(_check("VAL-053", "REQUIREMENTS", "warning", f"Дублирующееся требование: {text}.", "Объедините дубли требований.", ArtifactType.FUNCTIONAL_REQUIREMENTS.value))
        seen.add(text.lower())
        if "FR-" in str(requirement_id) and not row.get("acceptance_criteria"):
            checks.append(_check("VAL-054", "REQUIREMENTS", "warning", f"Требование {requirement_id} не имеет acceptance criteria.", "Добавьте acceptance criteria.", ArtifactType.FUNCTIONAL_REQUIREMENTS.value))
        if not (row.get("linked_use_case") or row.get("evidence") or row.get("assumption")):
            checks.append(_check("VAL-055", "REQUIREMENTS", "warning", f"Требование {requirement_id} не связано с use case/evidence/assumption.", "Добавьте linked_use_case, evidence или assumption=true.", ArtifactType.FUNCTIONAL_REQUIREMENTS.value))


def _check_final_bt(artifacts: dict[str, Any], checks: list[dict[str, Any]]) -> None:
    artifact = artifacts.get(ArtifactType.FINAL_BT.value)
    structured = _structured(artifact)
    if not artifact:
        checks.append(_check("VAL-060", "FINAL_BT", "warning", "Final BT ещё не собран.", "Соберите Final BT после заполнения этапов.", ArtifactType.FINAL_BT.value))
        return
    required_sections = {"context", "problem", "goal", "business_effect", "use_cases", "requirements"}
    section_ids = {section.get("id") for section in structured.get("sections") or [] if isinstance(section, dict)}
    missing = sorted(required_sections - section_ids)
    if missing:
        checks.append(_check("VAL-061", "FINAL_BT", "blocker", f"В Final BT отсутствуют обязательные разделы: {', '.join(missing)}.", "Пересоберите Final BT с обязательными разделами.", ArtifactType.FINAL_BT.value))
    dependencies = structured.get("artifact_versions") or {}
    for artifact_type, expected_version in dependencies.items():
        current_artifact = artifacts.get(str(artifact_type)) or {}
        current_version = current_artifact.get("version") if isinstance(current_artifact, dict) else None
        if current_version is not None and expected_version != current_version:
            checks.append(_check("VAL-062", "FINAL_BT", "blocker", f"Final BT содержит устаревшую зависимость {artifact_type}: {expected_version} != {current_version}.", "Обновите preview Final BT после изменения upstream artifact.", ArtifactType.FINAL_BT.value))
    if "unresolved_questions" not in structured:
        checks.append(_check("VAL-063", "FINAL_BT", "warning", "В Final BT явно не перечислены unresolved questions.", "Добавьте unresolved_questions, даже если список пуст.", ArtifactType.FINAL_BT.value))


def _check(
    check_id: str,
    stage: str,
    severity: str,
    message: str,
    recommendation: str,
    linked_artifact_type: str,
    evidence: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "id": check_id,
        "stage": stage,
        "severity": severity,
        "message": message,
        "recommendation": recommendation,
        "linked_artifact_type": linked_artifact_type,
        "evidence": evidence or [],
    }


def _score(checks: list[dict[str, Any]]) -> int:
    if any(check["severity"] == "blocker" for check in checks):
        return 0
    score = 100
    score -= 25 * sum(1 for check in checks if check["severity"] == "error")
    score -= 10 * sum(1 for check in checks if check["severity"] == "warning")
    return max(0, min(100, score))


def _next_actions(checks: list[dict[str, Any]]) -> list[str]:
    actions = []
    for check in checks:
        recommendation = check.get("recommendation")
        if recommendation and recommendation not in actions:
            actions.append(recommendation)
    return actions[:10]


def _structured(artifact: Any) -> dict[str, Any]:
    if isinstance(artifact, dict):
        structured = artifact.get("structured_content")
        if isinstance(structured, dict):
            return structured
        known_keys = {
            "readiness",
            "coverage",
            "source_trace",
            "problem_statement",
            "desired_outcome",
            "smart_analysis",
            "success_metrics",
            "qualitative_effects",
            "quantitative_metrics",
            "use_cases",
            "functional_requirements",
            "non_functional_requirements",
            "sections",
            "unresolved_questions",
            "artifact_versions",
        }
        if known_keys & set(artifact.keys()):
            return artifact
    return {}


def _content(artifact: Any) -> str:
    if isinstance(artifact, dict):
        return str(artifact.get("content") or "")
    return ""


def _has_any(structured: dict[str, Any], key: str) -> bool:
    value = structured.get(key)
    if isinstance(value, (list, dict, str)):
        return bool(value)
    return value is not None


def _has_key_summary(artifact: Any, key: str) -> bool:
    return isinstance(artifact, dict) and key in (artifact.get("structured_keys") or [])


def _contains_solution(text: str) -> bool:
    lowered = text.lower()
    return any(word in lowered for word in ("нужно внедрить", "решение", "автоматизировать", "создать систему", "implement"))
