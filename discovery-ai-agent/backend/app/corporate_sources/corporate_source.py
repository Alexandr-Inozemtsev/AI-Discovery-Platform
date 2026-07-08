from dataclasses import dataclass, field
from typing import Any, Literal


SourceType = Literal["confluence_page", "jira_issue", "git_file", "rag_chunk", "document", "link"]
ContentLevel = Literal["chunks", "extracted_text", "metadata_only"]
ExtractionStatus = Literal["completed", "failed", "metadata_only", "unsupported"]

SECRET_METADATA_KEYS = {
    "api_key",
    "apikey",
    "authorization",
    "cookie",
    "credential",
    "credentials",
    "password",
    "secret",
    "token",
}


@dataclass(frozen=True)
class CorporateSource:
    source_id: str
    source_type: SourceType
    source_name: str
    url: str = ""
    content_level: ContentLevel = "metadata_only"
    text_extraction_status: ExtractionStatus = "metadata_only"
    extracted_text: str = ""
    chunks: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    access_scope: str = "read-only"
    source_trace: list[dict[str, Any]] = field(default_factory=list)

    def to_public_dict(self, *, include_text: bool = False, max_text_chars: int = 1200) -> dict[str, Any]:
        payload = {
            "source_id": self.source_id,
            "source_type": self.source_type,
            "source_name": self.source_name,
            "url": self.url,
            "content_level": self.content_level,
            "text_extraction_status": self.text_extraction_status,
            "extracted_text": "",
            "chunks": _safe_chunks(self.chunks),
            "metadata": safe_metadata(self.metadata),
            "access_scope": self.access_scope,
            "source_trace": self.source_trace,
        }
        if include_text and self.content_level == "extracted_text":
            payload["extracted_text"] = (self.extracted_text or "")[:max_text_chars]
        return payload

    def to_evidence_dict(self) -> dict[str, Any] | None:
        if self.content_level == "metadata_only" or self.text_extraction_status != "completed":
            return None
        if self.content_level == "chunks" and not self.chunks:
            return None
        if self.content_level == "extracted_text" and not (self.extracted_text or "").strip():
            return None
        return {
            "source_id": self.source_id,
            "source_type": self.source_type,
            "source_name": self.source_name,
            "url": self.url,
            "content_level": self.content_level,
            "source_trace": self.source_trace,
        }


def safe_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    safe = {}
    for key, value in (metadata or {}).items():
        if str(key).lower() in SECRET_METADATA_KEYS:
            continue
        safe[str(key)] = value
    return safe


def _safe_chunks(chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    safe = []
    for chunk in chunks or []:
        if not isinstance(chunk, dict):
            continue
        safe.append(
            {
                "chunk_id": chunk.get("chunk_id") or chunk.get("id"),
                "source_id": chunk.get("source_id"),
                "order": chunk.get("order"),
                "text": chunk.get("text"),
            }
        )
    return safe
