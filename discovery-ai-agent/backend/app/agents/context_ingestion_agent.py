import json
from datetime import datetime

from app.agents.base_agent import BaseAgent


class ContextIngestionAgent(BaseAgent):
    artifact_type = "CONTEXT"

    def build_prompt(self, project, existing_artifacts: dict[str, str]) -> str:
        return f"Сделай ingestion контекста проекта {project.project_name}"

    def _deterministic_result(self, project, existing_artifacts: dict[str, str]) -> str:
        return ""

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

        source_trace = {
            "documents": [self._trace_document(d, i) for i, d in enumerate(documents)],
            "links": [self._trace_link(l, i) for i, l in enumerate(links)],
            "manual_context": {"used": any(bool(v) for v in overview_for_ai.values()), "fields": overview_for_ai},
            "previous_context": {
                "used": bool(previous_context),
                "has_extracted_knowledge": bool(previous_context.get("extracted_knowledge")),
                "history_count": len(previous_context.get("knowledge_history") or []),
                "has_previous_coverage": bool(previous_context.get("knowledge_coverage")),
                "has_previous_missing_information": bool(previous_context.get("missing_information")),
            },
        }

        prompt = (
            "Верни только JSON и строго на русском языке. "
            "Это этап ingestion, без рисков/рекомендаций/гипотез/TO-BE. "
            "Структура JSON: "
            "{\"процессы\":[],\"системы\":[],\"роли\":[],\"интеграции\":[],\"kpi\":[],\"бизнес_сущности\":[],\"документы\":[],\"термины\":[],"
            "\"missing_information\":[],\"покрытие\":{\"документы\":false,\"системы\":false,\"процессы\":false,\"bpmn\":false,\"kpi\":false,\"sla\":false}}. "
            f"Проект: {project.project_name}. "
            f"Обзор проекта: {json.dumps(overview_for_ai, ensure_ascii=False)}. "
            f"Ручной context_input: {json.dumps(context_input, ensure_ascii=False)}. "
            f"Документы (включая извлечённый текст/summary/chunks, если есть): {json.dumps(documents, ensure_ascii=False)}. "
            f"Ссылки (включая fetched text/summary/chunks, если есть): {json.dumps(links, ensure_ascii=False)}. "
            f"Предыдущий контекст проекта: {json.dumps(previous_context, ensure_ascii=False)}. "
            f"Source trace: {json.dumps(source_trace, ensure_ascii=False)}"
        )
        raw = self.llm.generate(prompt)
        extracted = self._json_from_llm_response(raw)
        if not extracted:
            raise ValueError("LLM вернул некорректный JSON")
        return {
            "extracted_knowledge": extracted,
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
        return {
            "id": d.get("id") or f"doc_{idx}",
            "name": d.get("name") or "Без названия",
            "source_type": d.get("type") or "file",
            "usage_mode": usage,
            "has_extracted_text": bool(extracted_text),
            "has_summary": bool(summary),
            "has_chunks": bool(chunks),
            "used": True,
            "reason": "Источник добавлен в ingestion payload",
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
        return {
            "id": l.get("id") or f"link_{idx}",
            "url": l.get("url") or str(link),
            "title": l.get("title") or "",
            "source_type": l.get("type") or l.get("source_type") or "url",
            "usage_mode": usage,
            "has_extracted_text": bool(extracted_text),
            "has_summary": bool(summary),
            "has_chunks": bool(chunks),
            "used": True,
            "reason": "Источник добавлен в ingestion payload",
        }

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
