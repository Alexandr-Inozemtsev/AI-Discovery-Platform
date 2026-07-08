import re
from typing import Any, Protocol

from app.agents.runtime import ToolAction, ToolPolicy
from app.corporate_sources.corporate_source import CorporateSource


class CorporateAdapter(Protocol):
    def search(self, request: dict[str, Any]) -> list[CorporateSource]:
        ...

    def read(self, request: dict[str, Any]) -> CorporateSource | None:
        ...


SECRET_KEYS = {"api_key", "apikey", "authorization", "cookie", "credential", "credentials", "password", "secret", "token"}


class CorporateToolGateway:
    def __init__(self, *, adapters: dict[str, CorporateAdapter], tool_policy: ToolPolicy | None = None):
        self.adapters = adapters
        self.tool_policy = tool_policy or ToolPolicy.for_ai_discovery_chat()
        self.safe_audit_log: list[dict[str, Any]] = []

    def handle_tool_request(self, request: dict[str, Any]) -> dict[str, Any]:
        tool_name = str(request.get("tool") or "")
        adapter_name = str(request.get("adapter") or "")
        if not self.tool_policy.is_allowed(ToolAction(name=tool_name, target=adapter_name or "corporate_tool_gateway")):
            self._log(tool_name, adapter_name, "denied", request, [])
            return {"ok": False, "error_code": "TOOL_POLICY_DENIED", "human_message": "Действие запрещено политикой доступа.", "sources": []}

        adapter = self.adapters.get(adapter_name)
        if not adapter:
            self._log(tool_name, adapter_name, "failed", request, [])
            return {"ok": False, "error_code": "ADAPTER_NOT_FOUND", "human_message": "Corporate adapter не подключен.", "sources": []}

        if tool_name.endswith(".read"):
            source = adapter.read(request)
            sources = [source] if source else []
        else:
            sources = adapter.search(request)
        normalized = [source.to_public_dict() for source in sources if source]
        self._log(tool_name, adapter_name, "success", request, sources)
        return {"ok": True, "sources": normalized}

    def _log(self, tool_name: str, adapter_name: str, status: str, request: dict[str, Any], sources: list[CorporateSource]) -> None:
        self.safe_audit_log.append(
            {
                "tool": tool_name,
                "adapter": adapter_name,
                "status": status,
                "request": mask_secrets(
                    {
                        "tool": request.get("tool"),
                        "adapter": request.get("adapter"),
                        "query_present": bool(request.get("query")),
                        "source_id": request.get("source_id"),
                    }
                ),
                "result_summary": [
                    {
                        "source_id": source.source_id,
                        "source_type": source.source_type,
                        "content_level": source.content_level,
                        "text_extraction_status": source.text_extraction_status,
                        "chunks_count": len(source.chunks or []),
                    }
                    for source in sources
                ],
            }
        )


def source_is_evidence(source: CorporateSource) -> bool:
    return source.to_evidence_dict() is not None


def mask_secrets(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            str(key): ("[redacted]" if _is_secret_key(key) else mask_secrets(nested))
            for key, nested in value.items()
        }
    if isinstance(value, list):
        return [mask_secrets(item) for item in value]
    if isinstance(value, str):
        text = re.sub(r"Bearer\s+[^\s,;]+", "Bearer [redacted]", value, flags=re.IGNORECASE)
        text = re.sub(r"\bsk-[A-Za-z0-9_\-]+", "[redacted]", text)
        return text
    return value


def _is_secret_key(key: Any) -> bool:
    normalized = str(key).lower()
    return normalized in SECRET_KEYS or any(marker in normalized for marker in ("token", "secret", "credential", "password", "cookie"))
