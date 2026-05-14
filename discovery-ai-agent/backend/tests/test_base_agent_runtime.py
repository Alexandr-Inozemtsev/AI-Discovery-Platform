import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.agents.base_agent import BaseAgent
from app.agents.goal_agent import GoalAgent
from app.agents.problem_agent import ProblemAgent
from app.agents.runtime import AgentResult


class FakeProject:
    id = "project_1"
    project_name = "Runtime Contract"


class StaticLLM:
    def __init__(self, response: str):
        self.response = response
        self.prompts = []

    def generate(self, prompt: str) -> str:
        self.prompts.append(prompt)
        return self.response


class FailingLLM:
    def __init__(self, message: str = "LLM unavailable"):
        self.message = message
        self.prompts = []

    def generate(self, prompt: str) -> str:
        self.prompts.append(prompt)
        raise RuntimeError(self.message)


class ContractAgent(BaseAgent):
    artifact_type = "CONTRACT"

    def build_prompt(self, project, existing_artifacts: dict[str, str]) -> str:
        return f"Prompt for {project.project_name}"

    def _deterministic_result(self, project, existing_artifacts: dict[str, str]) -> str:
        return f"Fallback for {project.project_name}"


def test_run_returns_llm_response_when_llm_returns_text():
    agent = ContractAgent(StaticLLM("LLM generated artifact"))

    assert agent.run(FakeProject(), {}) == "LLM generated artifact"


def test_run_uses_fallback_when_llm_raises_exception():
    agent = ContractAgent(FailingLLM())

    assert agent.run(FakeProject(), {}) == "Fallback for Runtime Contract"


def test_run_uses_fallback_when_llm_returns_empty_response():
    agent = ContractAgent(StaticLLM("   "))

    assert agent.run(FakeProject(), {}) == "Fallback for Runtime Contract"


def test_run_with_result_returns_agent_result():
    agent = ContractAgent(StaticLLM("LLM generated artifact"))

    result = agent.run_with_result(
        FakeProject(),
        {"CONTEXT": "Known context"},
        metadata={"trace_id": "trace_1"},
    )

    assert isinstance(result, AgentResult)
    assert result.ok is True
    assert result.content == "LLM generated artifact"
    assert result.structured_content is None
    assert result.raw_llm_response == "LLM generated artifact"
    assert result.used_fallback is False
    assert result.warnings == []
    assert result.errors == []
    assert result.source_trace == []
    assert result.metadata["trace_id"] == "trace_1"
    assert result.metadata["artifact_type"] == "CONTRACT"


def test_run_with_result_marks_fallback_on_exception():
    agent = ContractAgent(FailingLLM("Provider timeout"))

    result = agent.run_with_result(FakeProject(), {})

    assert result.ok is True
    assert result.content == "Fallback for Runtime Contract"
    assert result.raw_llm_response is None
    assert result.used_fallback is True
    assert result.warnings == ["LLM generation failed; deterministic fallback was used."]
    assert result.errors == ["Provider timeout"]


def test_problem_agent_and_goal_agent_do_not_crash_after_runtime_change():
    project = SimpleNamespace(project_name="Discovery MVP")
    existing = {"CONTEXT": "Контекст проекта"}

    assert ProblemAgent(StaticLLM("Generated problem")).run(project, existing) == "Generated problem"
    assert GoalAgent(StaticLLM("Generated goal")).run(project, existing) == "Generated goal"
