from dataclasses import dataclass, field
from typing import Any

from app.agents.runtime import ToolAction, ToolPolicy


SECRET_METADATA_KEYS = {"api_key", "apikey", "authorization", "cookie", "credential", "password", "secret", "token"}


@dataclass(frozen=True)
class CorporateSource:
    source_id: str
    source_type: str
    title: str
    url: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    text: str = ""

    def to_public_dict(self, *, include_text: bool = False, max_text_chars: int = 0) -> dict[str, Any]:
        payload = {
            "source_id": self.source_id,
            "source_type": self.source_type,
            "title": self.title,
            "url": self.url,
            "metadata": _safe_metadata(self.metadata),
        }
        if include_text and max_text_chars > 0:
            payload["text_preview"] = self.text[:max_text_chars]
        return payload


class CorporateToolGateway:
    def __init__(self, *, sources: list[CorporateSource] | None = None, tool_policy: ToolPolicy | None = None):
        self.sources = sources or []
        self.tool_policy = tool_policy or ToolPolicy.for_ai_discovery_chat()

    def is_allowed(self, action_name: str) -> bool:
        return self.tool_policy.is_allowed(ToolAction(name=action_name, target="corporate_tool_gateway"))

    def search(self, query: str, *, source_type: str | None = None, limit: int = 10) -> dict[str, Any]:
        if not self.is_allowed("rag.search"):
            return {"ok": False, "error": "Поиск запрещён политикой доступа.", "sources": []}
        normalized = (query or "").strip().lower()
        matches = []
        for source in self.sources:
            if source_type and source.source_type != source_type:
                continue
            haystack = f"{source.title} {source.url} {source.source_id}".lower()
            if not normalized or normalized in haystack:
                matches.append(source.to_public_dict())
            if len(matches) >= limit:
                break
        return {"ok": True, "sources": matches}

    def read(self, source_id: str, *, max_text_chars: int = 1200) -> dict[str, Any]:
        if not self.is_allowed("rag.read"):
            return {"ok": False, "error": "Чтение запрещено политикой доступа.", "source": None}
        for source in self.sources:
            if source.source_id == source_id:
                return {"ok": True, "source": source.to_public_dict(include_text=True, max_text_chars=max_text_chars)}
        return {"ok": False, "error": "Источник не найден.", "source": None}


def _safe_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    safe = {}
    for key, value in (metadata or {}).items():
        if str(key).lower() in SECRET_METADATA_KEYS:
            continue
        safe[key] = value
    return safe
