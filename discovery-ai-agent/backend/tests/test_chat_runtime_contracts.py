import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.agents.runtime import (
    StageProcessorRequest,
    StageProcessorResult,
    ToolAction,
    ToolPolicy,
)


def test_stage_processor_request_keeps_stage_inputs_and_excludes_secrets():
    request = StageProcessorRequest(
        project_id="project_1",
        artifact_type="PROBLEM",
        stage_type="PROBLEM",
        project_snapshot={"project_name": "AI Discovery"},
        input_artifacts={"CONTEXT": {"version": 2}},
        context_readiness={"status": "ready"},
        retrieval_result={"chunks": [{"source_id": "doc_1", "chunk_id": "c1"}]},
        user_answers=[{"question_id": "q1", "answer": "Нужно ускорить discovery"}],
        prompt_version="problem.v1",
        trace_id="trace_1",
        metadata={"actor": "ai_discovery_chat"},
    )

    assert request.project_id == "project_1"
    assert request.input_artifacts["CONTEXT"]["version"] == 2
    assert request.metadata["actor"] == "ai_discovery_chat"
    assert request.contains_secret_fields() is False


def test_stage_processor_request_detects_secret_like_fields():
    request = StageProcessorRequest(
        project_id="project_1",
        artifact_type="PROBLEM",
        stage_type="PROBLEM",
        metadata={"api_key": "sk-test"},
    )

    assert request.contains_secret_fields() is True


def test_stage_processor_result_returns_ru_human_message_and_patch_preview():
    result = StageProcessorResult(
        ok=True,
        artifact_type="PROBLEM",
        content="Проблема сформулирована.",
        structured_content={"problem_statement": "Проблема сформулирована."},
        proposed_patch={"problem_statement": "Проблема сформулирована."},
        preview={"target_artifact_type": "PROBLEM", "changed_fields": ["problem_statement"]},
        human_message="Черновик готов к проверке.",
        evidence=[{"source_id": "doc_1", "chunk_id": "c1", "source_name": "brief.md"}],
    )

    assert result.human_message == "Черновик готов к проверке."
    assert result.proposed_patch["problem_statement"] == "Проблема сформулирована."
    assert result.preview["changed_fields"] == ["problem_statement"]
    assert result.requires_apply_step() is True


def test_tool_policy_allows_preview_and_apply_but_blocks_direct_artifact_write():
    policy = ToolPolicy.for_ai_discovery_chat()

    assert policy.is_allowed(ToolAction(name="proposed_patch.create", target="PROBLEM"))
    assert policy.is_allowed(ToolAction(name="patch.preview", target="PROBLEM"))
    assert policy.is_allowed(ToolAction(name="patch.apply", target="PROBLEM", requires_user_confirmation=True))
    assert not policy.is_allowed(ToolAction(name="discovery_artifacts.write", target="PROBLEM"))
    assert not policy.is_allowed(ToolAction(name="patch.apply", target="PROBLEM", requires_user_confirmation=False))
