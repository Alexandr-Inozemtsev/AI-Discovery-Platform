import json
from datetime import datetime

from app.agents.base_agent import BaseAgent


class ContextIngestionAgent(BaseAgent):
    artifact_type = "CONTEXT"
    MAX_CONTEXT_CHARS = 30000
    MAX_SOURCE_CHARS = 6000
    MAX_CHUNKS_PER_SOURCE = 5

    def build_prompt(self, project, existing_artifacts: dict[str, str]) -> str:
        return f"Perform context ingestion for project {project.project_name}"

    def _deterministic_result(self, project, existing_artifacts: dict[str, str]) -> str:
        fallback = {
            "processes": [], "systems": [], "roles": [], "integrations": [], "kpi": [],
            "business_entities": [], "documents": [], "terms": [],
            "coverage": self._default_coverage(),
            "missing_information": ["Контекст не был проанализирован LLM, использован deterministic fallback."],
            "recommendations": [], "source_trace": []
        }
        return json.dumps(fallback, ensure_ascii=False)

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

        source_trace = [self._trace_document(d, i) for i, d in enumerate(documents)] + [self._trace_link(l, i) for i, l in enumerate(links)]
        missing_information = self._build_missing_information_from_sources(overview_for_ai, source_trace)

        compact_documents = [self._compact_source_for_prompt(d, "document") for d in documents]
        compact_links = [self._compact_source_for_prompt(l, "link") for l in links]
        compact_previous = self._truncate_str(json.dumps(previous_context, ensure_ascii=False), self.MAX_CONTEXT_CHARS // 2)
        compact_input = self._truncate_str(json.dumps(context_input, ensure_ascii=False), self.MAX_CONTEXT_CHARS // 3)

        prompt = (
            "Return only valid JSON. Do not return Markdown. JSON keys must be English. "
            "Array values must be in Russian. This is ingestion stage only: do not generate TO BE, requirements, solution, or separate risks section. "
            "Do not invent content for metadata-only sources. Use source_trace as truth boundary. "
            "If content_level=metadata_only, mention missing content in missing_information. "
            "Target JSON structure: "
            "{\"processes\":[],\"systems\":[],\"roles\":[],\"integrations\":[],\"kpi\":[],\"business_entities\":[],\"documents\":[],\"terms\":[],"
            "\"coverage\":{\"documents\":false,\"systems\":false,\"processes\":false,\"roles\":false,\"integrations\":false,\"bpmn\":false,\"kpi\":false,\"sla\":false,\"constraints\":false},"
            "\"missing_information\":[],\"recommendations\":[],"
            "\"problem_handoff\":{\"what_found\":[],\"key_facts\":[],\"constraints\":[],\"ambiguities\":[],\"questions_before_problem\":[]}}. "
            "For problem_handoff write only facts grounded in supplied context and source_trace. "
            "If data is insufficient, explicitly list missing facts in ambiguities and questions_before_problem. "
            f"Project: {project.project_name}. "
            f"Overview: {json.dumps(overview_for_ai, ensure_ascii=False)}. "
            f"Manual context_input: {compact_input}. "
            f"Documents: {json.dumps(compact_documents, ensure_ascii=False)}. "
            f"Links: {json.dumps(compact_links, ensure_ascii=False)}. "
            f"Previous context: {compact_previous}. "
            f"Source trace: {json.dumps(source_trace, ensure_ascii=False)}"
        )
        prompt = self._truncate_str(prompt, self.MAX_CONTEXT_CHARS)
        raw = self.llm.generate(prompt)
        extracted = self._json_from_llm_response(raw)
        normalized = self._normalize_extracted_knowledge(extracted)

        if not any(normalized.get(k) for k in ["processes", "systems", "roles", "integrations", "kpi", "business_entities", "documents", "terms"]):
            normalized = self._deterministic_fallback(overview_for_ai, source_trace, missing_information)

        normalized["missing_information"] = list(dict.fromkeys((normalized.get("missing_information") or []) + missing_information))
        normalized["source_trace"] = source_trace
        normalized["problem_handoff"] = self._normalize_problem_handoff(normalized.get("problem_handoff"), normalized, missing_information)

        return {
            "extracted_knowledge": normalized,
            "source_trace": source_trace,
            "overview_for_ai": overview_for_ai,
            "problem_handoff": normalized["problem_handoff"],
            "indexing_status": "completed",
            "analyzed_at": datetime.utcnow().isoformat(),
        }

    def _trace_document(self, doc, idx: int) -> dict:
        d = doc if isinstance(doc, dict) else {"name": str(doc)}
        content_level = self._detect_document_content_level(d)
        source_name = d.get("name") or "Без названия"
        used = content_level != "metadata_only"
        reason = f"Использовано содержимое источника: {content_level}." if used else f"Не извлечён текст документа: {source_name}. Пока использованы только метаданные файла."
        return {
            "source_type": "document",
            "source_id": d.get("id") or f"doc_{idx}",
            "source_name": source_name,
            "used": used,
            "content_level": content_level,
            "reason": reason,
        }

    def _trace_link(self, link, idx: int) -> dict:
        l = link if isinstance(link, dict) else {"url": str(link)}
        content_level = self._detect_link_content_level(l)
        source_name = l.get("title") or l.get("url") or str(link)
        used = content_level != "metadata_only"
        reason = f"Использовано содержимое источника: {content_level}." if used else f"Не получено содержимое ссылки: {source_name}. Пока использованы только URL/title."
        return {
            "source_type": "link",
            "source_id": l.get("id") or f"link_{idx}",
            "source_name": source_name,
            "used": used,
            "content_level": content_level,
            "reason": reason,
        }

    def _compact_source_for_prompt(self, source, source_type: str) -> dict:
        s = source if isinstance(source, dict) else {"raw": str(source)}
        content_level = self._detect_document_content_level(s) if source_type == "document" else self._detect_link_content_level(s)
        text = ""
        chunks = []
        if content_level == "text_content":
            text = str(s.get("text_content") or "")
        elif content_level == "extracted_text":
            text = str(s.get("extracted_text") or s.get("text") or "")
        elif content_level == "fetched_content":
            text = str(s.get("fetched_content") or "")
        elif content_level == "summary":
            text = str(s.get("summary") or "")
        elif content_level == "chunks":
            raw_chunks = s.get("chunks")
            if isinstance(raw_chunks, list):
                chunks = [self._truncate_str(str(c.get("text") if isinstance(c, dict) else c), self.MAX_SOURCE_CHARS // 3) for c in raw_chunks[: self.MAX_CHUNKS_PER_SOURCE]]
        return {
            "id": s.get("id"),
            "name": s.get("name") or s.get("title"),
            "url": s.get("url"),
            "source_type": s.get("type") or s.get("source_type") or ("file" if source_type == "document" else "url"),
            "kind": source_type,
            "content_level": content_level,
            "text": self._truncate_str(text, self.MAX_SOURCE_CHARS),
            "chunks": chunks,
        }

    def _build_missing_information_from_sources(self, overview_for_ai: dict, source_trace: list[dict]) -> list[str]:
        rows: list[str] = []
        if not any(str(v).strip() for v in overview_for_ai.values()):
            rows.append("Не заполнен ручной контекст проекта: краткое описание, цель продукта, бизнес-направление или ответственные.")
        for s in source_trace:
            if s.get("source_type") == "document" and s.get("content_level") == "metadata_only":
                rows.append(f"Не извлечён текст документа: {s.get('source_name')}. Пока использованы только метаданные файла.")
            if s.get("source_type") == "link" and s.get("content_level") == "metadata_only":
                rows.append(f"Не получено содержимое ссылки: {s.get('source_name')}. Пока использованы только URL/title.")
        return list(dict.fromkeys(rows))

    def _deterministic_fallback(self, overview_for_ai: dict, source_trace: list[dict], missing_information: list[str]) -> dict:
        docs = [s["source_name"] for s in source_trace if s["source_type"] == "document"]
        text_pool = " ".join([str(v) for v in overview_for_ai.values()] + [s.get("source_name", "") for s in source_trace]).lower()
        roles_present = bool(overview_for_ai.get("Бизнес-владелец процесса") or overview_for_ai.get("Ответственный за Discovery"))
        kpi_hint = any(x in text_pool for x in ["kpi", "метрик", "%", "сократить", "увеличить", "снизить", "повысить"])
        return {
            "processes": [], "systems": [], "roles": [], "integrations": [], "kpi": [],
            "business_entities": [], "documents": docs, "terms": [],
            "coverage": {
                **self._default_coverage(),
                "documents": bool(docs),
                "roles": roles_present,
                "kpi": kpi_hint,
                "bpmn": "bpmn" in text_pool,
                "sla": "sla" in text_pool,
                "constraints": any(x in text_pool for x in ["ограничени", "допущени", "нельзя", "запрещено"]),
            },
            "missing_information": list(dict.fromkeys(missing_information + (["Недостаточно данных в ручном описании контекста."] if not any(overview_for_ai.values()) else []))),
            "recommendations": [],
            "source_trace": source_trace,
            "problem_handoff": self._normalize_problem_handoff(None, {"documents": docs, "coverage": self._default_coverage()}, missing_information),
        }

    def _normalize_extracted_knowledge(self, data: dict) -> dict:
        d = data if isinstance(data, dict) else {}
        coverage = d.get("coverage") or d.get("покрытие") or {}
        return {
            "processes": self._to_list(d.get("processes") or d.get("процессы")),
            "systems": self._to_list(d.get("systems") or d.get("системы")),
            "roles": self._to_list(d.get("roles") or d.get("роли")),
            "integrations": self._to_list(d.get("integrations") or d.get("интеграции")),
            "kpi": self._to_list(d.get("kpi") or d.get("kpis")),
            "business_entities": self._to_list(d.get("business_entities") or d.get("бизнес_сущности")),
            "documents": self._to_list(d.get("documents") or d.get("документы")),
            "terms": self._to_list(d.get("terms") or d.get("термины")),
            "missing_information": self._to_list(d.get("missing_information") or d.get("недостающая_информация") or d.get("missingInfo")),
            "recommendations": self._to_list(d.get("recommendations") or d.get("рекомендации")),
            "problem_handoff": self._normalize_problem_handoff(d.get("problem_handoff") or d.get("problemHandoff") or d.get("выжимка_для_проблемы"), d, []),
            "source_trace": self._to_list(d.get("source_trace")),
            "coverage": {
                **self._default_coverage(),
                "documents": bool((coverage.get("documents") if isinstance(coverage, dict) else False) or (coverage.get("документы") if isinstance(coverage, dict) else False)),
                "systems": bool((coverage.get("systems") if isinstance(coverage, dict) else False) or (coverage.get("системы") if isinstance(coverage, dict) else False)),
                "processes": bool((coverage.get("processes") if isinstance(coverage, dict) else False) or (coverage.get("процессы") if isinstance(coverage, dict) else False)),
                "roles": bool((coverage.get("roles") if isinstance(coverage, dict) else False) or (coverage.get("роли") if isinstance(coverage, dict) else False)),
                "integrations": bool((coverage.get("integrations") if isinstance(coverage, dict) else False) or (coverage.get("интеграции") if isinstance(coverage, dict) else False)),
                "bpmn": bool((coverage.get("bpmn") if isinstance(coverage, dict) else False)),
                "kpi": bool((coverage.get("kpi") if isinstance(coverage, dict) else False)),
                "sla": bool((coverage.get("sla") if isinstance(coverage, dict) else False)),
                "constraints": bool((coverage.get("constraints") if isinstance(coverage, dict) else False) or (coverage.get("ограничения") if isinstance(coverage, dict) else False)),
            },
        }

    def _detect_document_content_level(self, source: dict) -> str:
        if source.get("text_content"):
            return "text_content"
        if source.get("extracted_text") or source.get("text"):
            return "extracted_text"
        if source.get("summary"):
            return "summary"
        if source.get("chunks"):
            return "chunks"
        return "metadata_only"

    def _detect_link_content_level(self, source: dict) -> str:
        if source.get("fetched_content"):
            return "fetched_content"
        if source.get("text_content"):
            return "text_content"
        if source.get("extracted_text") or source.get("text"):
            return "extracted_text"
        if source.get("summary"):
            return "summary"
        if source.get("chunks"):
            return "chunks"
        return "metadata_only"

    def _default_coverage(self) -> dict:
        return {"documents": False, "systems": False, "processes": False, "roles": False, "integrations": False, "bpmn": False, "kpi": False, "sla": False, "constraints": False}

    def _normalize_problem_handoff(self, value, knowledge: dict, missing_information: list[str]) -> dict:
        v = value if isinstance(value, dict) else {}
        key_facts = self._to_list(v.get("key_facts") or v.get("ключевые_факты"))
        if not key_facts:
            key_facts = []
            for key in ["processes", "systems", "roles", "integrations", "kpi", "business_entities", "documents", "terms"]:
                for item in self._to_list(knowledge.get(key))[:4]:
                    key_facts.append(str(item))
        ambiguities = self._to_list(v.get("ambiguities") or v.get("неясности")) + self._to_list(missing_information)
        questions = self._to_list(v.get("questions_before_problem") or v.get("что_уточнить") or v.get("questions"))
        if not questions and ambiguities:
            questions = ["Уточнить недостающие данные перед формулировкой проблемы."]
        return {
            "what_found": self._to_list(v.get("what_found") or v.get("что_найдено")) or key_facts[:5],
            "key_facts": list(dict.fromkeys([str(x) for x in key_facts]))[:20],
            "constraints": self._to_list(v.get("constraints") or v.get("ограничения")),
            "ambiguities": list(dict.fromkeys([str(x) for x in ambiguities]))[:20],
            "questions_before_problem": list(dict.fromkeys([str(x) for x in questions]))[:12],
        }

    def _to_list(self, value):
        if value is None:
            return []
        if isinstance(value, list):
            return value
        if isinstance(value, dict):
            return [value]
        return [str(value)]

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
