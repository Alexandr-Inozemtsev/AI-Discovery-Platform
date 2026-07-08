import re
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class RetrievalQuery:
    project_id: str
    query: str
    context_artifact: dict[str, Any]
    artifact_type: str | None = None
    stage: str | None = None
    filters: dict[str, Any] = field(default_factory=dict)
    top_k: int = 5
    max_chars: int = 12000
    trace_id: str | None = None


@dataclass
class RetrievedChunk:
    chunk_id: str
    source_id: str
    source_type: str
    source_name: str
    text: str
    score: float
    rank: int
    reason: str
    content_level: str
    chunk_order: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RetrievalResult:
    ok: bool
    query: str
    chunks: list[RetrievedChunk] = field(default_factory=list)
    source_trace: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "query": self.query,
            "chunks": [chunk.to_dict() for chunk in self.chunks],
            "source_trace": self.source_trace,
            "warnings": self.warnings,
            "errors": self.errors,
            "metadata": self.metadata,
        }


class SimpleRetriever:
    algorithm_version = "simple-keyword-v1"

    def retrieve(self, query: RetrievalQuery) -> RetrievalResult:
        if not query.context_artifact:
            return RetrievalResult(
                ok=False,
                query=query.query,
                errors=["CONTEXT_ARTIFACT_REQUIRED"],
                metadata=self._metadata(query, sources_seen=0, sources_used=0, candidates=0),
            )

        warnings: list[str] = []
        tokens = self._tokens(query.query)
        if not tokens:
            warnings.append("Пустой retrieval query: evidence может быть неполным.")

        sources = self._normalize_sources(query.context_artifact)
        candidates: list[RetrievedChunk] = []
        source_trace: list[dict[str, Any]] = []
        trace_by_source = self._trace_by_source(query.context_artifact)

        for source in sources:
            base_trace = dict(trace_by_source.get(source["source_id"], {}))
            if source["content_level"] == "metadata_only" or not source["chunks"]:
                warnings.append(f"Источник {source['source_name']} metadata-only и не используется как evidence.")
                source_trace.append(
                    {
                        **base_trace,
                        "source_id": source["source_id"],
                        "source_type": source["source_type"],
                        "source_name": source["source_name"],
                        "used": False,
                        "content_level": "metadata_only",
                        "reason": "Источник metadata-only исключён из evidence.",
                    }
                )
                continue

            for raw_chunk in source["chunks"]:
                text = str(raw_chunk.get("text") or "").strip()
                if not text:
                    continue
                score, reason = self._score(tokens, text, source)
                candidates.append(
                    RetrievedChunk(
                        chunk_id=str(raw_chunk.get("id") or raw_chunk.get("chunk_id") or f"{source['source_id']}:{raw_chunk.get('order', 0)}"),
                        source_id=source["source_id"],
                        source_type=source["source_type"],
                        source_name=source["source_name"],
                        text=text,
                        score=score,
                        rank=0,
                        reason=reason,
                        content_level=source["content_level"],
                        chunk_order=raw_chunk.get("order"),
                        metadata={"truncated": False},
                    )
                )

        ranked = sorted(candidates, key=lambda chunk: (-chunk.score, chunk.source_name, chunk.chunk_order or 0))
        selected = self._apply_budget(ranked[: max(1, query.top_k)], max(1, query.max_chars), warnings)
        for idx, chunk in enumerate(selected, start=1):
            chunk.rank = idx
            source_trace.append(
                {
                    "source_id": chunk.source_id,
                    "source_type": chunk.source_type,
                    "source_name": chunk.source_name,
                    "chunk_id": chunk.chunk_id,
                    "chunk_order": chunk.chunk_order,
                    "used": True,
                    "score": chunk.score,
                    "match_reason": chunk.reason,
                    "content_level": chunk.content_level,
                    "reason": "Источник использован retriever: найдено совпадение с запросом.",
                }
            )

        if not selected:
            warnings.append("Не найдено usable evidence chunks для запроса.")

        return RetrievalResult(
            ok=True,
            query=query.query,
            chunks=selected,
            source_trace=source_trace,
            warnings=list(dict.fromkeys(warnings)),
            metadata=self._metadata(
                query,
                sources_seen=len(sources),
                sources_used=len({chunk.source_id for chunk in selected}),
                candidates=len(candidates),
                returned=len(selected),
            ),
        )

    def _normalize_sources(self, context_artifact: dict[str, Any]) -> list[dict[str, Any]]:
        rows = []
        for key, source_type in (("uploaded_files", "document"), ("documents", "document"), ("links", "link")):
            values = context_artifact.get(key) if isinstance(context_artifact.get(key), list) else []
            for idx, value in enumerate(values):
                if not isinstance(value, dict):
                    value = {"name": str(value)}
                source_id = str(value.get("id") or f"{source_type}_{idx}")
                source_name = str(value.get("name") or value.get("title") or value.get("fileName") or value.get("url") or source_id)
                chunks = self._chunks_from_source(value, source_id)
                content_level = self._content_level(value, chunks)
                rows.append(
                    {
                        "source_id": source_id,
                        "source_type": source_type,
                        "source_name": source_name,
                        "content_level": content_level,
                        "text_extraction_status": value.get("text_extraction_status"),
                        "chunks": chunks,
                    }
                )
        return rows

    def _chunks_from_source(self, source: dict[str, Any], source_id: str) -> list[dict[str, Any]]:
        raw_chunks = source.get("chunks") if isinstance(source.get("chunks"), list) else []
        chunks: list[dict[str, Any]] = []
        for idx, chunk in enumerate(raw_chunks):
            if isinstance(chunk, dict):
                text = str(chunk.get("text") or "").strip()
                order = chunk.get("order", chunk.get("chunk_order", idx))
                chunk_id = chunk.get("id") or chunk.get("chunk_id") or f"{source_id}:{idx}"
            else:
                text = str(chunk).strip()
                order = idx
                chunk_id = f"{source_id}:{idx}"
            if text:
                chunks.append({"id": chunk_id, "text": text, "order": order})
        if chunks:
            return chunks
        for key in ("extracted_text", "text_content", "text", "fetched_content", "summary"):
            text = str(source.get(key) or "").strip()
            if text:
                return [{"id": f"{source_id}:0", "text": text, "order": 0}]
        return []

    def _content_level(self, source: dict[str, Any], chunks: list[dict[str, Any]]) -> str:
        status = source.get("text_extraction_status")
        if status and status != "completed":
            return "metadata_only"
        if chunks and isinstance(source.get("chunks"), list):
            return "chunks"
        for key in ("extracted_text", "text_content", "text", "fetched_content", "summary"):
            if str(source.get(key) or "").strip():
                return key
        return "metadata_only"

    def _trace_by_source(self, context_artifact: dict[str, Any]) -> dict[str, dict[str, Any]]:
        rows = context_artifact.get("source_trace") if isinstance(context_artifact.get("source_trace"), list) else []
        return {str(row.get("source_id")): row for row in rows if isinstance(row, dict) and row.get("source_id")}

    def _score(self, query_tokens: set[str], text: str, source: dict[str, Any]) -> tuple[float, str]:
        text_tokens = self._tokens(text)
        if not query_tokens:
            return (0.1, "empty_query_fallback")
        overlap = query_tokens.intersection(text_tokens)
        score = len(overlap) / max(1, len(query_tokens))
        name_overlap = query_tokens.intersection(self._tokens(source["source_name"]))
        if name_overlap:
            score += 0.1
        if source["content_level"] == "chunks":
            score += 0.05
        if len(text) < 20:
            score -= 0.1
        return (round(max(score, 0.01), 4), "keyword_overlap" if overlap else "low_confidence")

    def _apply_budget(self, chunks: list[RetrievedChunk], max_chars: int, warnings: list[str]) -> list[RetrievedChunk]:
        selected: list[RetrievedChunk] = []
        used_chars = 0
        for chunk in chunks:
            remaining = max_chars - used_chars
            if remaining <= 0:
                warnings.append("Retrieval result превышает budget и был обрезан.")
                break
            if len(chunk.text) > remaining:
                chunk.text = chunk.text[: max(0, remaining - 14)] + "...[truncated]"
                chunk.metadata["truncated"] = True
                warnings.append("Retrieval chunk был обрезан по budget.")
            used_chars += len(chunk.text)
            selected.append(chunk)
        return selected

    def _tokens(self, value: str) -> set[str]:
        return {token for token in re.split(r"[^0-9A-Za-zА-Яа-яЁё]+", (value or "").lower()) if len(token) > 2}

    def _metadata(self, query: RetrievalQuery, **kwargs: Any) -> dict[str, Any]:
        return {
            "trace_id": query.trace_id,
            "top_k": query.top_k,
            "max_chars": query.max_chars,
            "algorithm_version": self.algorithm_version,
            **kwargs,
        }
