from dataclasses import dataclass, field
from typing import Any


SECRET_FIELD_MARKERS = (
    "api_key",
    "apikey",
    "authorization",
    "bearer",
    "cookie",
    "credential",
    "password",
    "secret",
    "token",
)


def _contains_secret_marker(value: Any) -> bool:
    if isinstance(value, dict):
        for key, nested_value in value.items():
            normalized_key = str(key).lower()
            if any(marker in normalized_key for marker in SECRET_FIELD_MARKERS):
                return True
            if _contains_secret_marker(nested_value):
                return True
        return False
    if isinstance(value, list):
        return any(_contains_secret_marker(item) for item in value)
    return False


@dataclass
class StageProcessorRequest:
    project_id: str
    artifact_type: str
    stage_type: str
    project_snapshot: dict[str, Any] = field(default_factory=dict)
    input_artifacts: dict[str, Any] = field(default_factory=dict)
    context_readiness: dict[str, Any] = field(default_factory=dict)
    retrieval_result: dict[str, Any] | None = None
    user_answers: list[dict[str, Any]] = field(default_factory=list)
    prompt_version: str = ""
    trace_id: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def contains_secret_fields(self) -> bool:
        return _contains_secret_marker(
            {
                "project_snapshot": self.project_snapshot,
                "input_artifacts": self.input_artifacts,
                "context_readiness": self.context_readiness,
                "retrieval_result": self.retrieval_result,
                "user_answers": self.user_answers,
                "metadata": self.metadata,
            }
        )


@dataclass
class StageProcessorResult:
    ok: bool
    artifact_type: str
    content: str = ""
    structured_content: dict[str, Any] = field(default_factory=dict)
    proposed_patch: dict[str, Any] = field(default_factory=dict)
    preview: dict[str, Any] = field(default_factory=dict)
    human_message: str = ""
    evidence: list[dict[str, Any]] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    open_questions: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    used_fallback: bool = False
    source_trace: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def requires_apply_step(self) -> bool:
        return bool(self.proposed_patch)
