from abc import ABC, abstractmethod

from app.agents.runtime import AgentContext, AgentResult
from app.llm.base import BaseLLMClient


class BaseAgent(ABC):
    artifact_type: str

    def __init__(self, llm: BaseLLMClient):
        self.llm = llm

    @abstractmethod
    def build_prompt(self, project, existing_artifacts: dict[str, str]) -> str:
        raise NotImplementedError

    @abstractmethod
    def _deterministic_result(self, project, existing_artifacts: dict[str, str]) -> str:
        raise NotImplementedError

    def _build_context(
        self,
        project,
        existing_artifacts: dict[str, str],
        context_artifact=None,
        metadata: dict | None = None,
    ) -> AgentContext:
        return AgentContext(
            project=project,
            project_id=getattr(project, "id", None),
            artifact_type=self.artifact_type,
            existing_artifacts=existing_artifacts,
            context_artifact=context_artifact
            if context_artifact is not None
            else existing_artifacts.get("CONTEXT"),
            llm=self.llm,
            metadata=metadata or {},
        )

    def run_with_result(
        self,
        project,
        existing_artifacts: dict[str, str],
        context_artifact=None,
        metadata: dict | None = None,
    ) -> AgentResult:
        agent_context = self._build_context(project, existing_artifacts, context_artifact, metadata)
        result_metadata = {
            **agent_context.metadata,
            "artifact_type": agent_context.artifact_type,
            "project_id": agent_context.project_id,
        }
        prompt = self.build_prompt(project, existing_artifacts)
        try:
            raw_response = self.llm.generate(prompt)
        except Exception as exc:
            return self._fallback_result(
                project,
                existing_artifacts,
                result_metadata,
                raw_llm_response=None,
                warning="LLM generation failed; deterministic fallback was used.",
                error=str(exc),
            )

        content = (raw_response or "").strip()
        if content:
            return AgentResult(
                ok=True,
                content=content,
                raw_llm_response=raw_response,
                metadata=result_metadata,
            )

        return self._fallback_result(
            project,
            existing_artifacts,
            result_metadata,
            raw_llm_response=raw_response,
            warning="LLM returned empty response; deterministic fallback was used.",
        )

    def _fallback_result(
        self,
        project,
        existing_artifacts: dict[str, str],
        metadata: dict,
        raw_llm_response: str | None,
        warning: str,
        error: str | None = None,
    ) -> AgentResult:
        errors = [error] if error else []
        try:
            content = self._deterministic_result(project, existing_artifacts)
        except Exception as fallback_exc:
            return AgentResult(
                ok=False,
                content="",
                raw_llm_response=raw_llm_response,
                used_fallback=True,
                warnings=[warning, "Deterministic fallback failed."],
                errors=[*errors, str(fallback_exc)],
                metadata=metadata,
            )
        return AgentResult(
            ok=True,
            content=content,
            raw_llm_response=raw_llm_response,
            used_fallback=True,
            warnings=[warning],
            errors=errors,
            metadata=metadata,
        )

    def run(self, project, existing_artifacts: dict[str, str]) -> str:
        return self.run_with_result(project, existing_artifacts).content
