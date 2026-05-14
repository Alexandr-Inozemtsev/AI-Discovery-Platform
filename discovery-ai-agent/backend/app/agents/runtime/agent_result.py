from dataclasses import dataclass, field


@dataclass
class AgentResult:
    ok: bool
    content: str
    structured_content: dict | None = None
    raw_llm_response: str | None = None
    used_fallback: bool = False
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    source_trace: list[dict] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
