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

    assert fr.proposed_patch["functional_requirements"][0]["title"] == "система проверяет договор автоматически"
    assert fr.proposed_patch["functional_requirements"][0]["acceptance_criteria"]
    assert nfr.proposed_patch["non_functional_requirements"][0]["quality_attribute"]
    assert nfr.proposed_patch["non_functional_requirements"][0]["target"]
    assert final_bt.proposed_patch["document_preview"]["title"]
    assert final_bt.proposed_patch["validation_warnings"]


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
    assert result.proposed_patch == {}
    assert result.structured_content["validation_status"] == "requires_attention"
    assert result.structured_content["warnings"]
    assert "проверил" in result.human_message.lower()


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
