import json
from datetime import datetime

from app.agents.base_agent import BaseAgent


class ContextIngestionAgent(BaseAgent):
    artifact_type = "CONTEXT"
    MAX_CONTEXT_CHARS = 30000
    MAX_SOURCE_CHARS = 6000
    MAX_CHUNKS_PER_SOURCE = 5

    def build_prompt(self, project, existing_artifacts: dict[str, str]) -> str:
        return f"Сделай ingestion контекста проекта {project.project_name}"

    def _deterministic_result(self, project, existing_artifacts: dict[str, str]) -> str:
        return "{}"

    def analyze(self, project, payload: dict, previous_context: dict | None = None) -> dict:
        context_input = payload.get("context_input") or {}
        documents = payload.get("documents") or []
        links = payload.get("links") or []
        previous_context = previous_context or {}
        overview_for_ai = {
            "Краткое описание": context_input.get("short_description") or "",
            "Цель продукта / ожидаемый результат": context_input.get("product_goal") or context_input.get("initiative_goal") or "",
            "Бизнес-направление": context_input.get("business_domain") or "",
            "Бизнес-владелец процесса": context_input.get("business_process_owner") or context_input.get("process_owner") or "",
            "Ответственный за Discovery": context_input.get("discovery_responsible") or context_input.get("discovery_owner") or "",
        }

        doc_traces = [self._trace_document(d, i) for i, d in enumerate(documents)]
        link_traces = [self._trace_link(l, i) for i, l in enumerate(links)]
        source_trace = doc_traces + link_traces
        missing_information = []
        missing_information.extend([x["reason"] for x in doc_traces if not x["used"] and x["reason"]])
        missing_information.extend([x["reason"] for x in link_traces if not x["used"] and x["reason"]])

        compact_documents = [self._compact_source_for_prompt(d, "document") for d in documents]
        compact_links = [self._compact_source_for_prompt(l, "link") for l in links]
        compact_previous = self._truncate_str(json.dumps(previous_context, ensure_ascii=False), self.MAX_CONTEXT_CHARS // 2)
        compact_input = self._truncate_str(json.dumps(context_input, ensure_ascii=False), self.MAX_CONTEXT_CHARS // 3)

        prompt = (
            "Верни только JSON и строго на русском языке. "
            "Это этап ingestion, без рисков/рекомендаций/гипотез/TO-BE. "
            "Структура JSON: "
            "{\"процессы\":[],\"системы\":[],\"роли\":[],\"интеграции\":[],\"kpi\":[],\"бизнес_сущности\":[],\"документы\":[],\"термины\":[],"
            "\"missing_information\":[],\"покрытие\":{\"документы\":false,\"системы\":false,\"процессы\":false,\"bpmn\":false,\"kpi\":false,\"sla\":false}}. "
            f"Проект: {project.project_name}. "
            f"Обзор проекта: {json.dumps(overview_for_ai, ensure_ascii=False)}. "
            f"Ручной context_input: {compact_input}. "
            f"Документы (включая извлечённый текст/summary/chunks, если есть): {json.dumps(compact_documents, ensure_ascii=False)}. "
            f"Ссылки (включая fetched text/summary/chunks, если есть): {json.dumps(compact_links, ensure_ascii=False)}. "
            f"Предыдущий контекст проекта: {compact_previous}. "
            f"Source trace: {json.dumps(source_trace, ensure_ascii=False)}"
        )
        prompt = self._truncate_str(prompt, self.MAX_CONTEXT_CHARS)
        raw = self.llm.generate(prompt)
        extracted = self._json_from_llm_response(raw)
        normalized = self._normalize_extracted_knowledge(extracted)
        if not any(normalized.get(k) for k in ["процессы", "системы", "роли", "интеграции", "kpi", "бизнес_сущности", "документы", "термины"]):
            normalized = self._deterministic_fallback(overview_for_ai, source_trace, missing_information)
        normalized["missing_information"] = list(dict.fromkeys((normalized.get("missing_information") or []) + missing_information))
        return {
            "extracted_knowledge": normalized,
            "source_trace": source_trace,
            "overview_for_ai": overview_for_ai,
            "indexing_status": "completed",
            "analyzed_at": datetime.utcnow().isoformat(),
        }

    def _trace_document(self, doc, idx: int) -> dict:
        d = doc if isinstance(doc, dict) else {"name": str(doc)}
        extracted_text = d.get("extracted_text") or d.get("text")
        summary = d.get("summary")
        chunks = d.get("chunks")
        usage = "metadata_only"
        if extracted_text:
            usage = "full_text"
        elif summary:
            usage = "summary"
        elif chunks:
            usage = "chunks"
        source_name = d.get("name") or "Без названия"
        used = usage != "metadata_only"
        reason = "" if used else f"Не извлечён текст документа: {source_name}"
        return {
            "source_type": "document",
            "source_id": d.get("id") or f"doc_{idx}",
            "source_name": source_name,
            "used": used,
            "content_level": usage,
            "reason": reason,
        }

    def _trace_link(self, link, idx: int) -> dict:
        l = link if isinstance(link, dict) else {"url": str(link)}
        extracted_text = l.get("extracted_text") or l.get("text")
        summary = l.get("summary")
        chunks = l.get("chunks")
        usage = "metadata_only"
        if extracted_text:
            usage = "full_text"
        elif summary:
            usage = "summary"
        elif chunks:
            usage = "chunks"
        source_name = l.get("title") or l.get("url") or str(link)
        used = usage != "metadata_only"
        reason = "" if used else f"Не получено содержимое ссылки: {source_name}"
        return {
            "source_type": "link",
            "source_id": l.get("id") or f"link_{idx}",
            "source_name": source_name,
            "used": used,
            "content_level": usage,
            "reason": reason,
        }

    def _compact_source_for_prompt(self, source, source_type: str) -> dict:
        s = source if isinstance(source, dict) else {"raw": str(source)}
        chunks = s.get("chunks")
        if isinstance(chunks, list):
            chunks = [self._truncate_str(str(c), self.MAX_SOURCE_CHARS // 3) for c in chunks[: self.MAX_CHUNKS_PER_SOURCE]]
        return {
            "id": s.get("id"),
            "name": s.get("name") or s.get("title"),
            "url": s.get("url"),
            "source_type": s.get("type") or s.get("source_type") or ("file" if source_type == "document" else "url"),
            "kind": source_type,
            "text_content": self._truncate_str(str(s.get("text_content") or s.get("extracted_text") or s.get("text") or ""), self.MAX_SOURCE_CHARS),
            "summary": self._truncate_str(str(s.get("summary") or ""), self.MAX_SOURCE_CHARS // 2),
            "chunks": chunks or [],
        }

    def _deterministic_fallback(self, overview_for_ai: dict, source_trace: list[dict], missing_information: list[str]) -> dict:
        docs = [s["source_name"] for s in source_trace if s["source_type"] == "document"]
        links = [s["source_name"] for s in source_trace if s["source_type"] == "link"]
        return {
            "процессы": [],
            "системы": [],
            "роли": [],
            "интеграции": [],
            "kpi": [],
            "бизнес_сущности": [],
            "документы": docs,
            "термины": [],
            "missing_information": list(dict.fromkeys(missing_information + (["Недостаточно данных в ручном описании контекста."] if not any(overview_for_ai.values()) else []))),
            "покрытие": {"документы": bool(docs), "системы": False, "процессы": False, "bpmn": False, "kpi": False, "sla": False},
            "source_summary": {
                "total_sources": len(source_trace),
                "used_sources": len([s for s in source_trace if s.get("used")]),
                "metadata_only_sources": len([s for s in source_trace if s.get("content_level") == "metadata_only"]),
            },
        }

    def _normalize_extracted_knowledge(self, data: dict) -> dict:
        d = data if isinstance(data, dict) else {}
        coverage = d.get("покрытие") or d.get("coverage") or {}
        return {
            "процессы": d.get("процессы") or d.get("processes") or [],
            "системы": d.get("системы") or d.get("systems") or [],
            "роли": d.get("роли") or d.get("roles") or [],
            "интеграции": d.get("интеграции") or d.get("integrations") or [],
            "kpi": d.get("kpi") or d.get("kpis") or [],
            "бизнес_сущности": d.get("бизнес_сущности") or d.get("business_entities") or [],
            "документы": d.get("документы") or d.get("documents") or [],
            "термины": d.get("термины") or d.get("terms") or [],
            "missing_information": d.get("missing_information") or d.get("missingInfo") or [],
            "покрытие": {
                "документы": bool((coverage.get("документы") if isinstance(coverage, dict) else False) or (coverage.get("documents") if isinstance(coverage, dict) else False)),
                "системы": bool((coverage.get("системы") if isinstance(coverage, dict) else False) or (coverage.get("systems") if isinstance(coverage, dict) else False)),
                "процессы": bool((coverage.get("процессы") if isinstance(coverage, dict) else False) or (coverage.get("processes") if isinstance(coverage, dict) else False)),
                "bpmn": bool((coverage.get("bpmn") if isinstance(coverage, dict) else False)),
                "kpi": bool((coverage.get("kpi") if isinstance(coverage, dict) else False)),
                "sla": bool((coverage.get("sla") if isinstance(coverage, dict) else False)),
            },
        }

    def _truncate_str(self, value: str, max_chars: int) -> str:
        if len(value) <= max_chars:
            return value
        return value[:max_chars] + "...[truncated]"

    def _json_from_llm_response(self, raw: str) -> dict:
        txt = (raw or "").strip()
        if not txt:
            return {}
        try:
            return json.loads(txt)
        except Exception:
            start = txt.find("{")
            end = txt.rfind("}")
            if start < 0 or end < start:
                return {}
            try:
                return json.loads(txt[start : end + 1])
            except Exception:
                return {}
