from dataclasses import dataclass, field
from typing import Any

from app.llm.base import BaseLLMClient


@dataclass
class AgentContext:
    project: Any
    project_id: str | None
    artifact_type: str
    existing_artifacts: dict
    context_artifact: Any | None
    llm: BaseLLMClient
    metadata: dict = field(default_factory=dict)
