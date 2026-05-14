import json
from datetime import datetime

from app.agents.base_agent import BaseAgent


class ContextIngestionAgent(BaseAgent):
    artifact_type = "CONTEXT"
    MAX_CONTEXT_CHARS = 30000
    MAX_SOURCE_CHARS = 6000
    MAX_CHUNKS_PER_SOURCE = 5

    ARRAY_KEYS = [
        "processes",
        "systems",
        "roles",
        "integrations",
        "kpi",
        "business_entities",
        "documents",
        "terms",
        "constraints",
    ]

    def build_prompt(self, project, existing_artifacts: dict[str, str]) -> str:
        return f"Perform context ingestion for project {project.project_name}"

    def _deterministic_result(self, project, existing_artifacts: dict[str, str]) -> str:
        fallback = self._empty_contract()
        fallback["missing_information"] = [
            "Контекст не был проанализирован LLM, использован deterministic fallback."
        ]
        fallback["readiness"] = self._build_readiness(fallback["coverage"], fallback["missing_information"])
        fallback["problem_handoff"] = self._normalize_problem_handoff(None, fallback, fallback["missing_information"])
        return json.dumps(fallback, ensure_ascii=False)

    def analyze(self, project, payload: dict, previous_context: dict | None = None) -> dict:
        context_input = payload.get("context_input") or {}
        documents = payload.get("documents") or []
        links = payload.get("links") or []
        previous_context = previous_context or {}

        overview_for_ai = self._overview_for_ai(context_input)
        source_trace = [self._trace_document(d, i) for i, d in enumerate(documents)] + [
            self._trace_link(l, i) for i, l in enumerate(links)
        ]
        source_missing = self._build_missing_information_from_sources(overview_for_ai, source_trace)

        compact_documents = [self._compact_source_for_prompt(d, "document") for d in documents]
        compact_links = [self._compact_source_for_prompt(l, "link") for l in links]
        compact_previous = self._truncate_str(
            json.dumps(previous_context, ensure_ascii=False), self.MAX_CONTEXT_CHARS // 2
        )
        compact_input = self._truncate_str(
            json.dumps(context_input, ensure_ascii=False), self.MAX_CONTEXT_CHARS // 3
        )

        prompt = (
            "Return only valid JSON. Do not return Markdown. JSON keys must be English. "
            "Array values must be in Russian. This is Context ingestion stage only: "
            "do not generate TO-BE; do not generate solution; do not generate requirements; "
            "do not generate final BT; do not produce full risk analysis. "
            "Extract, normalize and assess completeness only. Do not invent content. "
            "Use extracted_text and chunks from documents when present. "
            "Do not count metadata-only sources as used. If content_level=metadata_only, "
            "mention missing content in missing_information and source_trace. "
            "Target JSON structure: "
            "{\"processes\":[],\"systems\":[],\"roles\":[],\"integrations\":[],\"kpi\":[],"
            "\"business_entities\":[],\"documents\":[],\"terms\":[],\"constraints\":[],"
            "\"coverage\":{\"manual_context\":false,\"documents\":false,\"systems\":false,"
            "\"processes\":false,\"roles\":false,\"integrations\":false,\"bpmn\":false,"
            "\"kpi\":false,\"sla\":false,\"constraints\":false},"
            "\"readiness\":{\"status\":\"ready|warning|blocked\",\"score\":0,"
            "\"can_go_to_problem\":false,\"summary\":\"\",\"blocking_reasons\":[],"
            "\"warnings\":[],\"next_actions\":[]},"
            "\"missing_information\":[],\"recommendations\":[],\"source_trace\":[],"
            "\"problem_handoff\":{\"context_summary\":\"\",\"known_processes\":[],"
            "\"known_systems\":[],\"known_roles\":[],\"known_integrations\":[],"
            "\"known_constraints\":[],\"known_kpi\":[],\"evidence\":[],\"open_questions\":[]}}. "
            "For problem_handoff write only facts grounded in supplied context and source_trace. "
            "If data is insufficient, explicitly list missing facts in open_questions. "
            f"Project: {project.project_name}. "
            f"Overview: {json.dumps(overview_for_ai, ensure_ascii=False)}. "
            f"Manual context_input: {compact_input}. "
            f"Documents: {json.dumps(compact_documents, ensure_ascii=False)}. "
            f"Links: {json.dumps(compact_links, ensure_ascii=False)}. "
            f"Previous context: {compact_previous}. "
            f"Source trace: {json.dumps(source_trace, ensure_ascii=False)}"
        )
        raw = self.llm.generate(self._truncate_str(prompt, self.MAX_CONTEXT_CHARS))
        extracted = self._json_from_llm_response(raw)
        normalized = self._normalize_extracted_knowledge(extracted)

        if not self._has_llm_content(normalized):
            normalized = self._deterministic_fallback(overview_for_ai, source_trace, source_missing)
        else:
            self._remove_unsupported_hallucinated_content(normalized, overview_for_ai, source_trace)

        normalized["source_trace"] = source_trace
        normalized["coverage"] = self._normalize_coverage(
            normalized.get("coverage"), normalized, overview_for_ai, source_trace
        )
        normalized["missing_information"] = list(
            dict.fromkeys(
                self._to_list(normalized.get("missing_information"))
                + source_missing
                + self._missing_information_from_coverage(normalized["coverage"])
            )
        )
        normalized["readiness"] = self._build_readiness(
            normalized["coverage"], normalized["missing_information"]
        )
        normalized["problem_handoff"] = self._normalize_problem_handoff(
            normalized.get("problem_handoff"), normalized, normalized["missing_information"]
        )

        return {
            "extracted_knowledge": normalized,
            "source_trace": source_trace,
            "coverage": normalized["coverage"],
            "readiness": normalized["readiness"],
            "overview_for_ai": overview_for_ai,
            "problem_handoff": normalized["problem_handoff"],
            "indexing_status": "completed",
            "analyzed_at": datetime.utcnow().isoformat(),
        }

    def _empty_contract(self) -> dict:
        return {
            "processes": [],
            "systems": [],
            "roles": [],
            "integrations": [],
            "kpi": [],
            "business_entities": [],
            "documents": [],
            "terms": [],
            "constraints": [],
            "coverage": self._default_coverage(),
            "readiness": self._default_readiness(),
            "missing_information": [],
            "recommendations": [],
            "source_trace": [],
            "problem_handoff": self._default_problem_handoff(),
        }

    def _overview_for_ai(self, context_input: dict) -> dict:
        return {
            "Краткое описание": context_input.get("short_description") or "",
            "Цель продукта / ожидаемый результат": context_input.get("product_goal")
            or context_input.get("initiative_goal")
            or "",
            "Бизнес-направление": context_input.get("business_domain") or "",
            "Связанные процессы": context_input.get("related_processes") or "",
            "Связанные системы": context_input.get("related_systems") or "",
            "Бизнес-владелец процесса": context_input.get("business_process_owner")
            or context_input.get("process_owner")
            or "",
            "Ответственный за Discovery": context_input.get("discovery_responsible")
            or context_input.get("discovery_owner")
            or "",
        }

    def _trace_document(self, doc, idx: int) -> dict:
        d = doc if isinstance(doc, dict) else {"name": str(doc)}
        content_level = self._detect_document_content_level(d)
        source_name = d.get("name") or d.get("title") or d.get("fileName") or "Без названия"
        extraction_status = d.get("text_extraction_status") or ("completed" if content_level != "metadata_only" else "not_available")
        used = content_level != "metadata_only" and extraction_status == "completed"
        if used:
            reason = f"Использовано содержимое источника: {content_level}."
        else:
            reason = (
                f"Не извлечён текст документа: {source_name}. "
                "Пока использованы только метаданные файла."
            )
        chunks = d.get("chunks") if isinstance(d.get("chunks"), list) else []
        return {
            "source_type": "document",
            "source_id": d.get("id") or f"doc_{idx}",
            "source_name": source_name,
            "used": used,
            "content_level": content_level if used else "metadata_only",
            "text_extraction_status": extraction_status,
            "text_extraction_error": d.get("text_extraction_error") or d.get("errorMessage"),
            "chunks_count": len(chunks),
            "reason": reason,
        }

    def _trace_link(self, link, idx: int) -> dict:
        l = link if isinstance(link, dict) else {"url": str(link)}
        content_level = self._detect_link_content_level(l)
        source_name = l.get("title") or l.get("url") or str(link)
        used = content_level != "metadata_only"
        reason = (
            f"Использовано содержимое источника: {content_level}."
            if used
            else f"Не получено содержимое ссылки: {source_name}. Пока использованы только URL/title."
        )
        chunks = l.get("chunks") if isinstance(l.get("chunks"), list) else []
        return {
            "source_type": "link",
            "source_id": l.get("id") or f"link_{idx}",
            "source_name": source_name,
            "used": used,
            "content_level": content_level,
            "chunks_count": len(chunks),
            "reason": reason,
        }

    def _compact_source_for_prompt(self, source, source_type: str) -> dict:
        s = source if isinstance(source, dict) else {"raw": str(source)}
        content_level = (
            self._detect_document_content_level(s)
            if source_type == "document"
            else self._detect_link_content_level(s)
        )
        raw_chunks = s.get("chunks") if isinstance(s.get("chunks"), list) else []
        chunks = [
            self._truncate_str(str(c.get("text") if isinstance(c, dict) else c), self.MAX_SOURCE_CHARS // 3)
            for c in raw_chunks[: self.MAX_CHUNKS_PER_SOURCE]
            if str(c.get("text") if isinstance(c, dict) else c).strip()
        ]
        text = (
            s.get("extracted_text")
            or s.get("text_content")
            or s.get("text")
            or s.get("fetched_content")
            or s.get("summary")
            or ""
        )
        return {
            "id": s.get("id"),
            "name": s.get("name") or s.get("title") or s.get("fileName"),
            "url": s.get("url"),
            "source_type": s.get("type") or s.get("source_type") or ("file" if source_type == "document" else "url"),
            "kind": source_type,
            "content_level": content_level,
            "text_extraction_status": s.get("text_extraction_status"),
            "text": self._truncate_str(str(text or ""), self.MAX_SOURCE_CHARS),
            "chunks": chunks,
        }

    def _build_missing_information_from_sources(self, overview_for_ai: dict, source_trace: list[dict]) -> list[str]:
        rows: list[str] = []
        if not any(str(v).strip() for v in overview_for_ai.values()):
            rows.append(
                "Не заполнен ручной контекст проекта: краткое описание, цель продукта, бизнес-направление или ответственные."
            )
        for source in source_trace:
            if source.get("source_type") == "document" and source.get("content_level") == "metadata_only":
                rows.append(
                    f"Не извлечён текст документа: {source.get('source_name')}. Пока использованы только метаданные файла."
                )
            if source.get("source_type") == "link" and source.get("content_level") == "metadata_only":
                rows.append(
                    f"Не получено содержимое ссылки: {source.get('source_name')}. Пока использованы только URL/title."
                )
        return list(dict.fromkeys(rows))

    def _deterministic_fallback(
        self,
        overview_for_ai: dict,
        source_trace: list[dict],
        missing_information: list[str],
    ) -> dict:
        result = self._empty_contract()
        result["documents"] = [
            str(source.get("source_name"))
            for source in source_trace
            if source.get("source_type") == "document" and source.get("used")
        ]
        result["coverage"] = self._normalize_coverage({}, result, overview_for_ai, source_trace)
        result["missing_information"] = list(dict.fromkeys(missing_information))
        result["source_trace"] = source_trace
        return result

    def _normalize_extracted_knowledge(self, data: dict) -> dict:
        d = data if isinstance(data, dict) else {}
        result = self._empty_contract()
        result.update(
            {
                "processes": self._to_list(d.get("processes") or d.get("процессы")),
                "systems": self._to_list(d.get("systems") or d.get("системы")),
                "roles": self._to_list(d.get("roles") or d.get("роли")),
                "integrations": self._to_list(d.get("integrations") or d.get("интеграции")),
                "kpi": self._to_list(d.get("kpi") or d.get("kpis")),
                "business_entities": self._to_list(d.get("business_entities") or d.get("бизнес_сущности")),
                "documents": self._to_list(d.get("documents") or d.get("документы")),
                "terms": self._to_list(d.get("terms") or d.get("термины")),
                "constraints": self._to_list(d.get("constraints") or d.get("ограничения")),
                "missing_information": self._to_list(
                    d.get("missing_information") or d.get("недостающая_информация") or d.get("missingInfo")
                ),
                "recommendations": self._to_list(d.get("recommendations") or d.get("рекомендации")),
                "problem_handoff": d.get("problem_handoff") or d.get("problemHandoff") or d.get("выжимка_для_проблемы") or {},
                "coverage": d.get("coverage") or d.get("покрытие") or {},
                "readiness": d.get("readiness") or {},
                "source_trace": self._to_list(d.get("source_trace")),
            }
        )
        return result

    def _normalize_coverage(
        self,
        value,
        knowledge: dict,
        overview_for_ai: dict,
        source_trace: list[dict],
    ) -> dict:
        v = value if isinstance(value, dict) else {}
        manual_context = any(str(item).strip() for item in overview_for_ai.values())
        used_documents = any(s.get("source_type") == "document" and s.get("used") for s in source_trace)
        return {
            **self._default_coverage(),
            "manual_context": bool(v.get("manual_context") or manual_context),
            "documents": bool(v.get("documents") or used_documents),
            "systems": bool(v.get("systems") or knowledge.get("systems") or overview_for_ai.get("Связанные системы")),
            "processes": bool(v.get("processes") or knowledge.get("processes") or overview_for_ai.get("Связанные процессы")),
            "roles": bool(
                v.get("roles")
                or knowledge.get("roles")
                or overview_for_ai.get("Бизнес-владелец процесса")
                or overview_for_ai.get("Ответственный за Discovery")
            ),
            "integrations": bool(v.get("integrations") or knowledge.get("integrations")),
            "bpmn": bool(v.get("bpmn")),
            "kpi": bool(v.get("kpi") or knowledge.get("kpi")),
            "sla": bool(v.get("sla")),
            "constraints": bool(v.get("constraints") or knowledge.get("constraints")),
        }

    def _build_readiness(self, coverage: dict, missing_information: list[str]) -> dict:
        weights = {
            "manual_context": 20,
            "documents": 10,
            "processes": 15,
            "systems": 15,
            "roles": 10,
            "integrations": 5,
            "kpi": 10,
            "constraints": 5,
            "bpmn": 5,
            "sla": 5,
        }
        score = sum(weight for key, weight in weights.items() if coverage.get(key))
        blocking_reasons: list[str] = []
        warnings: list[str] = []
        if not coverage.get("manual_context") and not coverage.get("documents"):
            blocking_reasons.append("Нет ручного контекста и нет источников с извлечённым текстом.")
        if not coverage.get("processes"):
            warnings.append("Не описаны бизнес-процессы.")
        if not coverage.get("systems"):
            warnings.append("Не указаны системы.")
        if not coverage.get("roles"):
            warnings.append("Не указаны роли или ответственные.")
        if not coverage.get("kpi"):
            warnings.append("Не указаны KPI или метрики успеха.")
        if not coverage.get("constraints"):
            warnings.append("Не описаны ограничения.")

        if blocking_reasons or score < 25:
            status = "blocked"
            can_go = False
            summary = "Контекст недостаточен для качественного анализа проблемы."
        elif score >= 70 and coverage.get("processes") and coverage.get("systems"):
            status = "ready"
            can_go = True
            summary = "Контекст достаточно покрыт для перехода к Problem stage."
        else:
            status = "warning"
            can_go = True
            summary = "Переход к Problem stage возможен, но качество анализа будет ограничено."

        next_actions = self._next_actions_from_gaps(coverage, missing_information)
        return {
            "status": status,
            "score": min(100, int(score)),
            "can_go_to_problem": can_go,
            "summary": summary,
            "blocking_reasons": blocking_reasons,
            "warnings": list(dict.fromkeys(warnings)),
            "next_actions": next_actions,
        }

    def _missing_information_from_coverage(self, coverage: dict) -> list[str]:
        rows: list[str] = []
        if not coverage.get("manual_context"):
            rows.append("Заполните ручное описание инициативы, цель, бизнес-домен и ответственных.")
        if not coverage.get("documents"):
            rows.append("Добавьте хотя бы один источник с извлечённым текстом или расширьте ручной контекст.")
        if not coverage.get("processes"):
            rows.append("Не хватает описания текущих бизнес-процессов.")
        if not coverage.get("systems"):
            rows.append("Не хватает списка затронутых систем.")
        if not coverage.get("roles"):
            rows.append("Не хватает ролей, участников или ответственных.")
        if not coverage.get("kpi"):
            rows.append("Не хватает KPI или измеримых метрик результата.")
        if not coverage.get("constraints"):
            rows.append("Не хватает ограничений, допущений или регуляторных рамок.")
        return rows

    def _next_actions_from_gaps(self, coverage: dict, missing_information: list[str]) -> list[str]:
        actions: list[str] = []
        if not coverage.get("manual_context"):
            actions.append("Заполнить краткое описание, цель, бизнес-домен и ответственных.")
        if not coverage.get("documents"):
            actions.append("Загрузить DOCX/TXT/MD/CSV/PDF/XLSX с извлекаемым текстом.")
        if not coverage.get("processes"):
            actions.append("Добавить описание текущего процесса или BPMN.")
        if not coverage.get("systems"):
            actions.append("Указать затронутые системы и каналы интеграции.")
        if not coverage.get("kpi"):
            actions.append("Уточнить KPI, SLA или измеримые критерии результата.")
        if not coverage.get("constraints"):
            actions.append("Добавить ограничения, допущения и регуляторные рамки.")
        for item in missing_information[:3]:
            if "Не извлечён текст документа" in item:
                actions.append("Заменить metadata-only документы на файлы с извлекаемым текстом.")
                break
        return list(dict.fromkeys(actions))[:8]

    def _normalize_problem_handoff(self, value, knowledge: dict, missing_information: list[str]) -> dict:
        v = value if isinstance(value, dict) else {}
        known_processes = self._to_list(v.get("known_processes") or v.get("processes") or knowledge.get("processes"))
        known_systems = self._to_list(v.get("known_systems") or v.get("systems") or knowledge.get("systems"))
        known_roles = self._to_list(v.get("known_roles") or v.get("roles") or knowledge.get("roles"))
        known_integrations = self._to_list(
            v.get("known_integrations") or v.get("integrations") or knowledge.get("integrations")
        )
        known_constraints = self._to_list(
            v.get("known_constraints") or v.get("constraints") or knowledge.get("constraints")
        )
        known_kpi = self._to_list(v.get("known_kpi") or v.get("kpi") or knowledge.get("kpi"))
        evidence = self._to_list(v.get("evidence"))
        if not evidence:
            evidence = [
                str(s.get("source_name"))
                for s in self._to_list(knowledge.get("source_trace"))
                if isinstance(s, dict) and s.get("used")
            ]
        context_summary = str(v.get("context_summary") or "").strip()
        if not context_summary:
            facts = known_processes[:2] + known_systems[:2] + known_roles[:2]
            context_summary = (
                "Из контекста извлечены факты: " + "; ".join(str(x) for x in facts)
                if facts
                else "Контекст пока содержит недостаточно подтверждённых фактов для Problem stage."
            )
        open_questions = self._to_list(
            v.get("open_questions")
            or v.get("questions_before_problem")
            or v.get("ambiguities")
            or v.get("questions")
        )
        open_questions = list(dict.fromkeys([str(x) for x in open_questions + missing_information]))[:20]
        return {
            "context_summary": context_summary,
            "known_processes": list(dict.fromkeys([str(x) for x in known_processes]))[:20],
            "known_systems": list(dict.fromkeys([str(x) for x in known_systems]))[:20],
            "known_roles": list(dict.fromkeys([str(x) for x in known_roles]))[:20],
            "known_integrations": list(dict.fromkeys([str(x) for x in known_integrations]))[:20],
            "known_constraints": list(dict.fromkeys([str(x) for x in known_constraints]))[:20],
            "known_kpi": list(dict.fromkeys([str(x) for x in known_kpi]))[:20],
            "evidence": list(dict.fromkeys([str(x) for x in evidence]))[:20],
            "open_questions": open_questions,
        }

    def _remove_unsupported_hallucinated_content(
        self, normalized: dict, overview_for_ai: dict, source_trace: list[dict]
    ) -> None:
        has_manual = any(str(v).strip() for v in overview_for_ai.values())
        has_used_source = any(s.get("used") for s in source_trace)
        if has_manual or has_used_source:
            return
        for key in self.ARRAY_KEYS:
            normalized[key] = []

    def _has_llm_content(self, normalized: dict) -> bool:
        if any(normalized.get(key) for key in self.ARRAY_KEYS):
            return True
        coverage = normalized.get("coverage")
        if isinstance(coverage, dict) and any(bool(v) for v in coverage.values()):
            return True
        return bool(normalized.get("problem_handoff"))

    def _detect_document_content_level(self, source: dict) -> str:
        status = source.get("text_extraction_status")
        if status and status != "completed":
            return "metadata_only"
        if str(source.get("extracted_text") or source.get("text") or "").strip():
            return "extracted_text"
        if str(source.get("text_content") or "").strip():
            return "text_content"
        chunks = source.get("chunks")
        if isinstance(chunks, list) and any(
            str(c.get("text") if isinstance(c, dict) else c).strip() for c in chunks
        ):
            return "chunks"
        if str(source.get("summary") or "").strip():
            return "summary"
        return "metadata_only"

    def _detect_link_content_level(self, source: dict) -> str:
        if str(source.get("fetched_content") or "").strip():
            return "fetched_content"
        if str(source.get("text_content") or "").strip():
            return "text_content"
        if str(source.get("extracted_text") or source.get("text") or "").strip():
            return "extracted_text"
        if str(source.get("summary") or "").strip():
            return "summary"
        chunks = source.get("chunks")
        if isinstance(chunks, list) and any(
            str(c.get("text") if isinstance(c, dict) else c).strip() for c in chunks
        ):
            return "chunks"
        return "metadata_only"

    def _default_coverage(self) -> dict:
        return {
            "manual_context": False,
            "documents": False,
            "systems": False,
            "processes": False,
            "roles": False,
            "integrations": False,
            "bpmn": False,
            "kpi": False,
            "sla": False,
            "constraints": False,
        }

    def _default_readiness(self) -> dict:
        return {
            "status": "blocked",
            "score": 0,
            "can_go_to_problem": False,
            "summary": "",
            "blocking_reasons": [],
            "warnings": [],
            "next_actions": [],
        }

    def _default_problem_handoff(self) -> dict:
        return {
            "context_summary": "",
            "known_processes": [],
            "known_systems": [],
            "known_roles": [],
            "known_integrations": [],
            "known_constraints": [],
            "known_kpi": [],
            "evidence": [],
            "open_questions": [],
        }

    def _to_list(self, value):
        if value is None:
            return []
        if isinstance(value, list):
            return value
        if isinstance(value, tuple):
            return list(value)
        if isinstance(value, dict):
            return [value]
        return [str(value)]

    def _truncate_str(self, value: str, max_chars: int) -> str:
        value = value or ""
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
