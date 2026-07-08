import json
from typing import Any

from app.agents.runtime import StageProcessorRequest, StageProcessorResult
from app.llm.base import BaseLLMClient
from app.models.discovery import ArtifactType


GROUNDING_FIELDS = {"evidence", "assumptions", "open_questions", "source_trace"}
PROMPT_VERSIONS = {
    ArtifactType.PROBLEM.value: "problem.v1",
    ArtifactType.GOAL.value: "goal.v1",
    ArtifactType.BUSINESS_EFFECT.value: "business_effect.v1",
    ArtifactType.USE_CASES.value: "use_cases.v1",
}
PROMPT_TEMPLATES = {
    "problem.v1": (
        "Ты Product AI Processor этапа Problem. Верни только структурированный JSON по контракту Problem. "
        "Не выдумывай факты без evidence; если evidence недостаточно, заполни assumptions/open_questions."
    ),
    "goal.v1": (
        "Ты Product AI Processor этапа Goal. Верни только структурированный JSON по контракту Goal/SMART. "
        "Опирайся на evidence и upstream artifacts; неподтвержденное помечай как assumption."
    ),
    "business_effect.v1": (
        "Ты Product AI Processor этапа Business Effect. Верни только структурированный JSON по контракту эффектов. "
        "Количественные метрики не выдумывай без evidence."
    ),
    "use_cases.v1": (
        "Ты Product AI Processor этапа Use Cases. Верни только структурированный JSON по контракту UC cards. "
        "Сценарии должны быть связаны с evidence или явно помечены assumption."
    ),
}


class StageDraftProcessor:
    supported_artifact_types = {
        ArtifactType.PROBLEM.value,
        ArtifactType.GOAL.value,
        ArtifactType.BUSINESS_EFFECT.value,
        ArtifactType.USE_CASES.value,
    }

    def __init__(self, llm_client: BaseLLMClient | None = None):
        self.llm_client = llm_client

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

        prompt_version = request.prompt_version or PROMPT_VERSIONS[request.artifact_type]
        prompt = build_stage_prompt(request, prompt_version)
        text = clean_stage_text(str(request.metadata.get("message") or ""))
        evidence = evidence_from_request(request)
        assumptions, open_questions = grounding_notes(evidence)
        source_trace = source_trace_from_request(request)
        warnings = []
        if not evidence:
            warnings.append("Недостаточно evidence для уверенного заполнения этапа; вывод помечен как assumption.")
        llm_output = self._generate_with_llm(prompt)
        llm_patch = parse_llm_patch(llm_output, request.artifact_type)

        if request.artifact_type == ArtifactType.PROBLEM.value:
            patch = {
                "problem_statement": text,
                "user_pains": [first_evidence_text(evidence) or text],
                "business_pains": ["Ручной процесс создаёт задержки и требует подтверждения business owner."],
                "root_causes": ["Ручной или неавтоматизированный процесс требует проверки на источниках."],
                "consequences_if_not_solved": ["Сохранится риск задержек, ошибок и повторных обращений."],
            }
        elif request.artifact_type == ArtifactType.GOAL.value:
            patch = {
                "desired_outcome": text,
                "smart_analysis": {
                    "specific": text,
                    "measurable": "Метрика требует подтверждения источниками.",
                    "achievable": "Достижимость нужно проверить с владельцами процесса.",
                    "relevant": "Цель связана с заявленным Discovery контекстом.",
                    "time_bound": "Срок требует уточнения.",
                },
                "success_metrics": [{"name": "Сокращение ручных операций", "target": "Требует подтверждения", "unit": "%"}],
                "non_goals": ["Автоматизация смежных процессов вне подтверждённого scope."],
                "constraints": ["Сроки, системы-источники и владельцы данных требуют уточнения."],
            }
        elif request.artifact_type == ArtifactType.BUSINESS_EFFECT.value:
            patch = {
                "qualitative_effects": [text],
                "quantitative_metrics": [{"metric": "Экономия времени", "value": "Требует расчёта", "confidence": "assumption"}],
                "risk_reduction": ["Снижение риска ручных ошибок требует подтверждения evidence."],
                "operational_effect": ["Сокращение повторных ручных проверок."],
                "measurement_method": ["Сравнить baseline времени обработки до/после внедрения."],
            }
        else:
            patch = {
                "use_cases": [
                    {
                        "id": "UC-001",
                        "title": text,
                        "actor": "Пользователь процесса",
                        "goal": text,
                        "trigger": "Пользователь запускает обработку бизнес-задачи.",
                        "preconditions": ["Данные по задаче доступны в системах-источниках."],
                        "main_flow": ["Открыть задачу", "Проверить данные", "Подтвердить результат"],
                        "alternative_flows": ["Если данные неполные, запросить уточнение у владельца процесса."],
                        "exceptions": ["Нет данных в источниках", "Требуется ручное подтверждение"],
                        "postconditions": ["Результат проверки зафиксирован в structured artifact."],
                        "evidence": evidence,
                        "assumptions": assumptions,
                    }
                ]
            }

        if llm_patch:
            patch.update(llm_patch)
        patch.update({"evidence": evidence, "assumptions": assumptions, "open_questions": open_questions})
        return result_from_patch(
            request.artifact_type,
            patch,
            source_trace,
            warnings=warnings,
            prompt_version=prompt_version,
            prompt=prompt,
            used_fallback=not bool(llm_patch),
            llm_output=llm_output,
            used_inputs={
                "project_snapshot": bool(request.project_snapshot),
                "input_artifacts": True,
                "context_readiness": True,
                "retrieval_result": request.retrieval_result is not None,
                "user_answers": True,
            },
        )

    def _generate_with_llm(self, prompt: str) -> str:
        if not self.llm_client:
            return ""
        try:
            return self.llm_client.generate(prompt)
        except Exception:
            return ""


def result_from_patch(
    artifact_type: str,
    patch: dict[str, Any],
    source_trace: list[dict[str, Any]],
    warnings: list[str] | None = None,
    prompt_version: str = "",
    prompt: str = "",
    used_fallback: bool = False,
    llm_output: str = "",
    used_inputs: dict[str, bool] | None = None,
) -> StageProcessorResult:
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
        warnings=warnings or [],
        used_fallback=used_fallback,
        source_trace=source_trace,
        human_message="Я подготовил черновик изменения. Проверьте preview перед применением.",
        metadata={
            "processor": "stage_draft_processor",
            "prompt_version": prompt_version,
            "prompt_template": prompt,
            "llm_used": bool(llm_output),
            "used_inputs": used_inputs or {},
        },
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
        if chunk.get("content_level") == "metadata_only":
            continue
        text = str(chunk.get("text") or "").strip()
        if not text:
            continue
        evidence.append(
            {
                "source_id": chunk.get("source_id"),
                "chunk_id": chunk.get("chunk_id") or chunk.get("id"),
                "source_name": chunk.get("source_name") or chunk.get("name"),
                "text": text,
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
        return str(patch.get("desired_outcome") or patch.get("recommended_goal") or "")
    if artifact_type == ArtifactType.BUSINESS_EFFECT.value:
        return "; ".join(str(item) for item in patch.get("qualitative_effects") or patch.get("qualitative_effect") or [])
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


def build_stage_prompt(request: StageProcessorRequest, prompt_version: str) -> str:
    return "\n".join(
        [
            PROMPT_TEMPLATES.get(prompt_version, ""),
            f"prompt_version: {prompt_version}",
            f"artifact_type: {request.artifact_type}",
            f"project_snapshot: {request.project_snapshot}",
            f"input_artifacts: {request.input_artifacts}",
            f"context_readiness: {request.context_readiness}",
            f"retrieval_result: {request.retrieval_result}",
            f"user_answers: {request.user_answers}",
            f"user_message: {request.metadata.get('message') if request.metadata else ''}",
        ]
    )


def parse_llm_patch(raw: str, artifact_type: str) -> dict[str, Any]:
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
    except Exception:
        return {}
    if not isinstance(parsed, dict):
        return {}
    allowed_fields = {
        ArtifactType.PROBLEM.value: {
            "problem_statement",
            "user_pains",
            "business_pains",
            "root_causes",
            "consequences_if_not_solved",
        },
        ArtifactType.GOAL.value: {
            "desired_outcome",
            "smart_analysis",
            "success_metrics",
            "non_goals",
            "constraints",
        },
        ArtifactType.BUSINESS_EFFECT.value: {
            "qualitative_effects",
            "quantitative_metrics",
            "risk_reduction",
            "operational_effect",
            "measurement_method",
        },
        ArtifactType.USE_CASES.value: {"use_cases"},
    }.get(artifact_type, set())
    return {key: value for key, value in parsed.items() if key in allowed_fields}
