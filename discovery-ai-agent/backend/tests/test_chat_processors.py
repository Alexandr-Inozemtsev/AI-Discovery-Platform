import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.agents.runtime import StageProcessorRequest
from app.assistant.discovery_chat_orchestrator import DiscoveryChatOrchestrator
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


def test_stage_draft_processor_builds_structured_problem_goal_effect_and_use_cases():
    processor = StageDraftProcessor()

    problem = processor.process(_request(ArtifactType.PROBLEM, "Проблема: ручная проверка договора задерживает клиента"))
    goal = processor.process(_request(ArtifactType.GOAL, "Цель: сократить ручную проверку до 1 дня"))
    effect = processor.process(_request(ArtifactType.BUSINESS_EFFECT, "Эффект: меньше повторных визитов и ошибок"))
    use_cases = processor.process(_request(ArtifactType.USE_CASES, "Сценарий: менеджер продлевает договор"))

    assert problem.proposed_patch["problem_statement"] == "ручная проверка договора задерживает клиента"
    assert problem.proposed_patch["pains"]
    assert problem.proposed_patch["root_causes"]
    assert goal.proposed_patch["recommended_goal"] == "сократить ручную проверку до 1 дня"
    assert goal.proposed_patch["smart"]["specific"]
    assert goal.proposed_patch["kpi"]
    assert effect.proposed_patch["qualitative_effect"]
    assert effect.proposed_patch["metrics"]
    assert use_cases.proposed_patch["use_cases"][0]["flow"]
    assert use_cases.proposed_patch["use_cases"][0]["linked_requirements"]


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
    assert "qualitative_effect" in result.proposed_patch
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
