from typing import Any

from app.corporate_sources.corporate_source import CorporateSource


class GitAdapter:
    def __init__(self, sources: list[CorporateSource] | None = None):
        self.sources = sources or []

    def search(self, request: dict[str, Any]) -> list[CorporateSource]:
        query = str(request.get("query") or "").lower().strip()
        return [
            source
            for source in self.sources
            if source.source_type == "git_file" and (not query or query in f"{source.source_name} {source.url}".lower())
        ]

    def read(self, request: dict[str, Any]) -> CorporateSource | None:
        source_id = request.get("source_id")
        return next((source for source in self.sources if source.source_id == source_id), None)
