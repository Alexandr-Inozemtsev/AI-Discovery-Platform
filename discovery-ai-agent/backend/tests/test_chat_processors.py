import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.agents.runtime import StageProcessorRequest
from app.assistant.discovery_chat_orchestrator import DiscoveryChatOrchestrator
from app.llm.base import BaseLLMClient
from app.models.discovery import ArtifactType
from app.processors import RequirementsProcessor, StageDraftProcessor, ValidationProcessor


def _request(artifact_type: ArtifactType, message: str = "Сократить ручные операции и задержки") -> StageProcessorRequest:
    return StageProcessorRequest(
        project_id="project_1",
        artifact_type=artifact_type.value,
        stage_type=artifact_type.value,
        project_snapshot={"project_name": "ИБС", "business_domain": "Банк"},
        retrieval_result={
            "chunks": [
                {
                    "source_id": "doc_1",
                    "chunk_id": "c1",
                    "source_name": "brief.md",
                    "text": "Оператор вручную проверяет договор, клиенты жалуются на задержки.",
                }
            ],
            "source_trace": [{"source_id": "doc_1", "chunk_id": "c1", "used": True}],
        },
        metadata={"message": message},
    )


class JsonLLMClient(BaseLLMClient):
    def __init__(self, response: str):
        self.response = response
        self.last_prompt = ""

    def generate(self, prompt: str) -> str:
        self.last_prompt = prompt
        return self.response


def test_stage_draft_processor_builds_structured_problem_goal_effect_and_use_cases():
    processor = StageDraftProcessor()

    problem = processor.process(_request(ArtifactType.PROBLEM, "Проблема: ручная проверка договора задерживает клиента"))
    goal = processor.process(_request(ArtifactType.GOAL, "Цель: сократить ручную проверку до 1 дня"))
    effect = processor.process(_request(ArtifactType.BUSINESS_EFFECT, "Эффект: меньше повторных визитов и ошибок"))
    use_cases = processor.process(_request(ArtifactType.USE_CASES, "Сценарий: менеджер продлевает договор"))

    assert problem.proposed_patch["problem_statement"] == "ручная проверка договора задерживает клиента"
    assert problem.proposed_patch["user_pains"]
    assert problem.proposed_patch["business_pains"]
    assert problem.proposed_patch["root_causes"]
    assert goal.proposed_patch["desired_outcome"] == "сократить ручную проверку до 1 дня"
    assert goal.proposed_patch["smart_analysis"]["specific"]
    assert goal.proposed_patch["success_metrics"]
    assert effect.proposed_patch["qualitative_effects"]
    assert effect.proposed_patch["quantitative_metrics"]
    assert use_cases.proposed_patch["use_cases"][0]["main_flow"]
    assert use_cases.proposed_patch["use_cases"][0]["id"] == "UC-001"


def test_stage_draft_processor_returns_target_structured_contracts_and_prompt_versions():
    processor = StageDraftProcessor()

    problem = processor.process(_request(ArtifactType.PROBLEM, "Проблема: ручная проверка договора задерживает клиента"))
    goal = processor.process(_request(ArtifactType.GOAL, "Цель: сократить ручную проверку до 1 дня"))
    effect = processor.process(_request(ArtifactType.BUSINESS_EFFECT, "Эффект: меньше повторных визитов и ошибок"))
    use_cases = processor.process(_request(ArtifactType.USE_CASES, "Сценарий: менеджер продлевает договор"))

    assert problem.proposed_patch.keys() >= {
        "problem_statement",
        "user_pains",
        "business_pains",
        "root_causes",
        "consequences_if_not_solved",
        "evidence",
        "assumptions",
        "open_questions",
    }
    assert goal.proposed_patch.keys() >= {
        "desired_outcome",
        "smart_analysis",
        "success_metrics",
        "non_goals",
        "constraints",
        "evidence",
        "assumptions",
        "open_questions",
    }
    assert effect.proposed_patch.keys() >= {
        "qualitative_effects",
        "quantitative_metrics",
        "risk_reduction",
        "operational_effect",
        "measurement_method",
        "evidence",
        "assumptions",
        "open_questions",
    }
    assert use_cases.proposed_patch["use_cases"][0].keys() >= {
        "id",
        "title",
        "actor",
        "goal",
        "trigger",
        "preconditions",
        "main_flow",
        "alternative_flows",
        "exceptions",
        "postconditions",
        "evidence",
        "assumptions",
    }
    assert problem.metadata["prompt_version"] == "problem.v1"
    assert goal.metadata["prompt_version"] == "goal.v1"
    assert effect.metadata["prompt_version"] == "business_effect.v1"
    assert use_cases.metadata["prompt_version"] == "use_cases.v1"
    assert problem.metadata["used_inputs"]["project_snapshot"] is True
    assert problem.metadata["used_inputs"]["input_artifacts"] is True
    assert problem.metadata["used_inputs"]["context_readiness"] is True
    assert problem.metadata["used_inputs"]["user_answers"] is True


def test_stage_draft_processor_no_evidence_sets_open_questions_warnings_and_fallback():
    processor = StageDraftProcessor()
    request = StageProcessorRequest(
        project_id="project_1",
        artifact_type=ArtifactType.PROBLEM.value,
        stage_type=ArtifactType.PROBLEM.value,
        project_snapshot={"project_name": "ИБС"},
        input_artifacts={"CONTEXT": {"structured_keys": ["readiness"]}},
        context_readiness={"status": "low"},
        retrieval_result={"chunks": [], "source_trace": []},
        user_answers=[{"question": "Где болит?", "answer": "В ручной проверке"}],
        metadata={"message": "Проблема: ручная проверка договора"},
    )

    result = processor.process(request)

    assert result.ok is True
    assert result.evidence == []
    assert result.open_questions
    assert result.warnings
    assert result.assumptions
    assert result.used_fallback is True
    assert result.proposed_patch["open_questions"] == result.open_questions


def test_stage_draft_processor_ignores_metadata_only_sources_as_evidence():
    processor = StageDraftProcessor()
    request = StageProcessorRequest(
        project_id="project_1",
        artifact_type=ArtifactType.GOAL.value,
        stage_type=ArtifactType.GOAL.value,
        project_snapshot={"project_name": "ИБС"},
        retrieval_result={
            "chunks": [
                {
                    "source_id": "doc_meta",
                    "chunk_id": "m1",
                    "source_name": "scan.pdf",
                    "content_level": "metadata_only",
                    "text": "Название файла без извлечённого текста",
                },
                {
                    "source_id": "doc_empty",
                    "chunk_id": "e1",
                    "source_name": "empty.md",
                    "text": "",
                },
            ],
            "source_trace": [{"source_id": "doc_meta", "content_level": "metadata_only", "used": False}],
        },
        metadata={"message": "Цель: сократить ручную проверку"},
    )

    result = processor.process(request)

    assert result.evidence == []
    assert result.proposed_patch["evidence"] == []
    assert result.open_questions
    assert result.warnings


def test_stage_draft_processor_uses_llm_boundary_when_valid_json_is_returned():
    llm = JsonLLMClient(
        '{"problem_statement":"LLM уточнила проблему","user_pains":["Оператор тратит время"],'
        '"business_pains":["Высокая стоимость обработки"],"root_causes":["Нет автоматической проверки"],'
        '"consequences_if_not_solved":["Задержки сохранятся"]}'
    )
    processor = StageDraftProcessor(llm_client=llm)

    result = processor.process(_request(ArtifactType.PROBLEM, "Проблема: ручная проверка договора"))

    assert "problem.v1" in llm.last_prompt
    assert result.used_fallback is False
    assert result.proposed_patch["problem_statement"] == "LLM уточнила проблему"
    assert result.proposed_patch["user_pains"] == ["Оператор тратит время"]
    assert result.proposed_patch["evidence"]


def test_requirements_processor_builds_fr_nfr_and_final_bt_patches():
    processor = RequirementsProcessor()

    fr = processor.process(_request(ArtifactType.FUNCTIONAL_REQUIREMENTS, "Требование: система проверяет договор автоматически"))
    nfr = processor.process(_request(ArtifactType.NON_FUNCTIONAL_REQUIREMENTS, "НФТ: ответ проверки до 3 секунд"))
    final_bt = processor.process(_request(ArtifactType.FINAL_BT, "Финальный БТ: подготовь документ по пролонгации"))

    assert fr.proposed_patch["functional_requirements"][0]["text"] == "система проверяет договор автоматически"
    assert fr.proposed_patch["functional_requirements"][0]["acceptance_criteria"]
    assert nfr.proposed_patch["non_functional_requirements"][0]["category"]
    assert nfr.proposed_patch["non_functional_requirements"][0]["target_value"]
    assert final_bt.proposed_patch["sections"]
    assert final_bt.proposed_patch["validation_summary"]


def test_requirements_processor_generates_fr_from_use_cases_with_required_contract():
    processor = RequirementsProcessor()
    request = StageProcessorRequest(
        project_id="project_1",
        artifact_type=ArtifactType.FUNCTIONAL_REQUIREMENTS.value,
        stage_type=ArtifactType.FUNCTIONAL_REQUIREMENTS.value,
        project_snapshot={"project_name": "ИБС"},
        input_artifacts={
            ArtifactType.PROBLEM.value: {"structured_content": {"problem_statement": "Ручная проверка задерживает клиента"}},
            ArtifactType.GOAL.value: {"structured_content": {"desired_outcome": "Сократить ручную проверку"}},
            ArtifactType.USE_CASES.value: {
                "structured_content": {
                    "use_cases": [
                        {
                            "id": "UC-001",
                            "title": "Менеджер проверяет договор",
                            "goal": "Проверить договор автоматически",
                        }
                    ]
                }
            },
        },
        retrieval_result={
            "chunks": [
                {
                    "source_id": "doc_1",
                    "chunk_id": "c1",
                    "source_name": "brief.md",
                    "text": "Менеджер должен видеть результат автоматической проверки договора.",
                }
            ],
            "source_trace": [{"source_id": "doc_1", "chunk_id": "c1", "used": True}],
        },
        metadata={"message": "Требование: система проверяет договор автоматически"},
    )

    result = processor.process(request)
    requirement = result.proposed_patch["functional_requirements"][0]

    assert result.ok is True
    assert result.requires_apply_step() is True
    assert requirement == {
        "id": "FR-001",
        "text": "система проверяет договор автоматически",
        "priority": "MUST",
        "linked_use_case": "UC-001",
        "acceptance_criteria": ["Результат автоматической проверки договора доступен пользователю процесса."],
        "business_rules": ["Требование должно быть связано с подтверждённой проблемой, целью или use case."],
        "evidence": result.evidence,
        "assumption": False,
        "open_questions": [],
    }
    assert result.metadata["prompt_version"] == "functional_requirements.v1"


def test_requirements_processor_marks_requirement_without_evidence_as_assumption():
    processor = RequirementsProcessor()
    request = StageProcessorRequest(
        project_id="project_1",
        artifact_type=ArtifactType.NON_FUNCTIONAL_REQUIREMENTS.value,
        stage_type=ArtifactType.NON_FUNCTIONAL_REQUIREMENTS.value,
        project_snapshot={"project_name": "ИБС"},
        input_artifacts={
            ArtifactType.PROBLEM.value: {"structured_content": {"problem_statement": "Ручной процесс"}},
            ArtifactType.GOAL.value: {"structured_content": {"desired_outcome": "Ускорить проверку"}},
        },
        retrieval_result={"chunks": [], "source_trace": []},
        metadata={"message": "НФТ: ответ проверки до 3 секунд"},
    )

    result = processor.process(request)
    requirement = result.proposed_patch["non_functional_requirements"][0]

    assert requirement["id"] == "NFR-001"
    assert requirement["category"] == "performance"
    assert requirement["text"] == "ответ проверки до 3 секунд"
    assert requirement["target_value"] == "до 3 секунд"
    assert requirement["evidence"] == []
    assert requirement["assumption"] is True
    assert result.assumptions
    assert result.open_questions
    assert result.warnings


def test_requirements_processor_preserves_stable_ids_on_update():
    processor = RequirementsProcessor()
    request = StageProcessorRequest(
        project_id="project_1",
        artifact_type=ArtifactType.FUNCTIONAL_REQUIREMENTS.value,
        stage_type=ArtifactType.FUNCTIONAL_REQUIREMENTS.value,
        input_artifacts={
            ArtifactType.PROBLEM.value: {"structured_content": {"problem_statement": "Ручной процесс"}},
            ArtifactType.GOAL.value: {"structured_content": {"desired_outcome": "Ускорить проверку"}},
            ArtifactType.USE_CASES.value: {
                "structured_content": {"use_cases": [{"id": "UC-001", "title": "Проверить договор"}]}
            },
            ArtifactType.FUNCTIONAL_REQUIREMENTS.value: {
                "structured_content": {
                    "functional_requirements": [
                        {
                            "id": "FR-007",
                            "text": "система проверяет договор автоматически",
                            "linked_use_case": "UC-001",
                        }
                    ]
                }
            },
        },
        retrieval_result={
            "chunks": [{"source_id": "doc_1", "chunk_id": "c1", "text": "Система проверяет договор автоматически."}],
            "source_trace": [{"source_id": "doc_1", "chunk_id": "c1"}],
        },
        metadata={"message": "Требование: система проверяет договор автоматически"},
    )

    result = processor.process(request)

    assert result.proposed_patch["functional_requirements"][0]["id"] == "FR-007"


def test_requirements_processor_final_bt_includes_validation_warnings_and_unresolved_questions():
    processor = RequirementsProcessor()
    request = StageProcessorRequest(
        project_id="project_1",
        artifact_type=ArtifactType.FINAL_BT.value,
        stage_type=ArtifactType.FINAL_BT.value,
        project_snapshot={"project_name": "ИБС"},
        input_artifacts={
            ArtifactType.CONTEXT.value: {"content": "Контекст проекта", "structured_content": {"open_questions": ["Уточнить источник данных"]}},
            ArtifactType.PROBLEM.value: {"content": "Проблема ручной проверки", "structured_content": {"open_questions": ["Кто владелец процесса?"]}},
            ArtifactType.GOAL.value: {"content": "Цель сократить проверку", "structured_content": {}},
            ArtifactType.BUSINESS_EFFECT.value: {"content": "Снижение задержек", "structured_content": {}},
            ArtifactType.USE_CASES.value: {"content": "UC-001 Проверить договор", "structured_content": {}},
            ArtifactType.FUNCTIONAL_REQUIREMENTS.value: {"content": "FR-001 Система проверяет договор", "structured_content": {}},
            ArtifactType.VALIDATION_REPORT.value: {
                "structured_content": {
                    "warnings": ["Не хватает evidence по NFR"],
                    "blockers": ["Не заполнены риски"],
                }
            },
        },
        retrieval_result={
            "chunks": [{"source_id": "doc_1", "chunk_id": "c1", "text": "Финальный документ должен включать unresolved вопросы."}],
            "source_trace": [{"source_id": "doc_1", "chunk_id": "c1"}],
        },
        metadata={"message": "Финальный БТ: собрать документ"},
    )

    result = processor.process(request)
    patch = result.proposed_patch

    assert [section["id"] for section in patch["sections"]] == [
        "context",
        "problem",
        "goal",
        "business_effect",
        "use_cases",
        "requirements",
    ]
    assert patch["validation_summary"]["warnings"] == ["Не хватает evidence по NFR"]
    assert patch["validation_summary"]["blockers"] == ["Не заполнены риски"]
    assert "Уточнить источник данных" in patch["unresolved_questions"]
    assert "Кто владелец процесса?" in patch["unresolved_questions"]
    assert patch["evidence_summary"]
    assert result.requires_apply_step() is True


def test_discovery_chat_orchestrator_uses_stage_processors_for_structured_patches():
    orchestrator = DiscoveryChatOrchestrator()

    result = orchestrator.handle_message(
        project=SimpleNamespace(id="project_1", project_name="ИБС", business_domain="Банк"),
        message="@business-effect Эффект: меньше повторных визитов",
        artifact_type=None,
        context_artifact={},
        artifacts={},
    )["result"]

    assert result.artifact_type == ArtifactType.BUSINESS_EFFECT.value
    assert "qualitative_effects" in result.proposed_patch
    assert "content" not in result.proposed_patch


def test_validation_processor_builds_validation_report_without_applying_patch():
    processor = ValidationProcessor()
    request = StageProcessorRequest(
        project_id="project_1",
        artifact_type=ArtifactType.VALIDATION_REPORT.value,
        stage_type=ArtifactType.VALIDATION_REPORT.value,
        input_artifacts={
            "PROBLEM": {"version": 1, "structured_keys": ["problem_statement"]},
            "GOAL": {"version": 1, "structured_keys": []},
            "FUNCTIONAL_REQUIREMENTS": {"version": 1, "structured_keys": []},
        },
        metadata={"message": "@critic проверь качество"},
    )

    result = processor.process(request)

    assert result.ok is True
    assert result.artifact_type == ArtifactType.VALIDATION_REPORT.value
    assert result.proposed_patch["overall_status"] == "blocked"
    assert result.structured_content["overall_status"] == "blocked"
    assert result.structured_content["warnings"]
    assert "проверил" in result.human_message.lower()


def test_validation_processor_empty_project_returns_blocked_report():
    processor = ValidationProcessor()

    result = processor.process(
        StageProcessorRequest(
            project_id="project_1",
            artifact_type=ArtifactType.VALIDATION_REPORT.value,
            stage_type=ArtifactType.VALIDATION_REPORT.value,
            input_artifacts={},
            metadata={"message": "@critic проверь качество"},
        )
    )

    report = result.proposed_patch
    assert result.ok is True
    assert result.requires_apply_step() is True
    assert report["overall_status"] == "blocked"
    assert report["score"] == 0
    assert report["blockers"]
    assert any(check["stage"] == "CONTEXT" for check in report["checks"])
    assert all(check.keys() >= {"id", "stage", "severity", "message", "recommendation", "linked_artifact_type", "evidence"} for check in report["checks"])


def test_validation_processor_missing_goal_kpi_returns_warning_and_next_action():
    processor = ValidationProcessor()
    request = StageProcessorRequest(
        project_id="project_1",
        artifact_type=ArtifactType.VALIDATION_REPORT.value,
        stage_type=ArtifactType.VALIDATION_REPORT.value,
        input_artifacts={
            ArtifactType.PROBLEM.value: {"structured_content": {"problem_statement": "Ручная проверка задерживает клиента", "user_pains": ["Ожидание"], "root_causes": ["Ручной процесс"], "evidence": [{"source_id": "doc_1"}]}},
            ArtifactType.GOAL.value: {"structured_content": {"desired_outcome": "Сократить ручную проверку", "smart_analysis": {"specific": "Да"}, "open_questions": []}},
        },
    )

    result = processor.process(request)
    report = result.proposed_patch

    assert report["overall_status"] == "warning"
    assert any(check["stage"] == "GOAL" and check["severity"] == "warning" for check in report["checks"])
    assert any("KPI" in action or "open_questions" in action for action in report["next_actions"])


def test_validation_processor_requirements_without_evidence_return_warning():
    processor = ValidationProcessor()
    request = StageProcessorRequest(
        project_id="project_1",
        artifact_type=ArtifactType.VALIDATION_REPORT.value,
        stage_type=ArtifactType.VALIDATION_REPORT.value,
        input_artifacts={
            ArtifactType.PROBLEM.value: {"structured_content": {"problem_statement": "Ручная проверка", "assumptions": ["Подтвердить"]}},
            ArtifactType.GOAL.value: {"structured_content": {"desired_outcome": "Сократить проверку", "success_metrics": [{"name": "Время"}]}},
            ArtifactType.FUNCTIONAL_REQUIREMENTS.value: {
                "structured_content": {
                    "functional_requirements": [
                        {
                            "id": "FR-001",
                            "text": "Система проверяет договор",
                            "priority": "MUST",
                            "acceptance_criteria": ["Результат доступен"],
                            "linked_use_case": None,
                            "evidence": [],
                            "assumption": False,
                        }
                    ]
                }
            },
        },
    )

    result = processor.process(request)
    report = result.proposed_patch

    assert any(check["stage"] == "REQUIREMENTS" and check["severity"] == "warning" for check in report["checks"])
    assert "Требование FR-001 не связано с use case/evidence/assumption." in report["warnings"]


def test_validation_processor_stale_dependency_returns_blocker():
    processor = ValidationProcessor()
    request = StageProcessorRequest(
        project_id="project_1",
        artifact_type=ArtifactType.VALIDATION_REPORT.value,
        stage_type=ArtifactType.VALIDATION_REPORT.value,
        input_artifacts={
            ArtifactType.FINAL_BT.value: {
                "version": 1,
                "structured_content": {
                    "sections": [
                        {"id": "context", "title": "Контекст", "content": "ok"},
                        {"id": "problem", "title": "Проблема", "content": "ok"},
                        {"id": "goal", "title": "Цель", "content": "ok"},
                        {"id": "business_effect", "title": "Бизнес-эффект", "content": "ok"},
                        {"id": "use_cases", "title": "Use Cases", "content": "ok"},
                        {"id": "requirements", "title": "Требования", "content": "ok"},
                    ],
                    "artifact_versions": {ArtifactType.PROBLEM.value: 1},
                    "unresolved_questions": [],
                },
            },
            ArtifactType.PROBLEM.value: {"version": 2, "structured_content": {"problem_statement": "Обновлённая проблема"}},
        },
    )

    result = processor.process(request)
    report = result.proposed_patch

    assert report["overall_status"] == "blocked"
    assert any("stale" in blocker.lower() or "устар" in blocker.lower() for blocker in report["blockers"])


def test_discovery_chat_orchestrator_critic_returns_validation_report_patch():
    orchestrator = DiscoveryChatOrchestrator()

    result = orchestrator.handle_message(
        project=SimpleNamespace(id="project_1", project_name="ИБС", business_domain="Банк"),
        message="@critic проверь качество",
        artifact_type=None,
        context_artifact={},
        artifacts={},
    )["result"]

    assert result.artifact_type == ArtifactType.VALIDATION_REPORT.value
    assert result.proposed_patch["overall_status"] == "blocked"
    assert result.requires_apply_step() is True


def test_orchestrator_does_not_build_domain_patch_without_processor():
    orchestrator = DiscoveryChatOrchestrator()

    result = orchestrator.handle_message(
        project=SimpleNamespace(id="project_1", project_name="ИБС", business_domain="Банк"),
        message="@context найди gaps",
        artifact_type=None,
        context_artifact={},
        artifacts={},
    )["result"]

    assert result.artifact_type == ArtifactType.CONTEXT.value
    assert result.proposed_patch == {}
    assert result.human_message == "Для этого этапа AI Chat пока не формирует patch. Я могу показать состояние или предложить уточняющие вопросы."
