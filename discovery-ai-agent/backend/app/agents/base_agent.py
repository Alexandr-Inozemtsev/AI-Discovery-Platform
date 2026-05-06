from abc import ABC, abstractmethod

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

    def run(self, project, existing_artifacts: dict[str, str]) -> str:
        prompt = self.build_prompt(project, existing_artifacts)
        _ = self.llm.generate(prompt)
        return self._deterministic_result(project, existing_artifacts)
