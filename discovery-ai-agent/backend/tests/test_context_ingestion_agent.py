import json
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.agents.context_ingestion_agent import ContextIngestionAgent


class FakeProject:
    project_name = "Автопролонгация ИБС"


class StaticLLM:
    def __init__(self, response: str):
        self.response = response
        self.last_prompt = ""

    def generate(self, prompt: str) -> str:
        self.last_prompt = prompt
        return self.response


class InvalidJsonLLM:
    def __init__(self):
        self.last_prompt = ""

    def generate(self, prompt: str) -> str:
        self.last_prompt = prompt
        return "not a json response"


def _agent_with_response(payload: dict):
    llm = StaticLLM(json.dumps(payload, ensure_ascii=False))
    return ContextIngestionAgent(llm), llm


def _minimal_payload():
    return {"context_input": {"short_description": "Автоматизация автопролонгации ИБС"}, "documents": [], "links": []}


def test_analyze_returns_english_contract_keys():
    llm_payload = {
        "processes": ["Регистрация ИБС"],
        "systems": ["SFA"],
        "roles": ["Клиентский менеджер"],
        "integrations": ["Pega"],
        "kpi": ["Сократить ручные операции на 80%"],
        "business_entities": ["Договор ИБС"],
        "documents": ["BRD.pdf"],
        "terms": ["Автопролонгация"],
        "coverage": {"documents": True, "systems": True, "processes": True, "roles": True, "integrations": True, "bpmn": False, "kpi": True, "sla": False, "constraints": False},
        "missing_information": [],
        "recommendations": [],
    }
    agent, _ = _agent_with_response(llm_payload)
    result = agent.analyze(FakeProject(), _minimal_payload(), previous_context={})
    ek = result["extracted_knowledge"]

    expected_keys = {"processes", "systems", "roles", "integrations", "kpi", "business_entities", "documents", "terms", "coverage", "missing_information", "recommendations", "source_trace"}
    assert expected_keys.issubset(ek.keys())
    for ru_key in ["процессы", "системы", "роли", "интеграции", "бизнес_сущности", "документы", "термины", "покрытие"]:
        assert ru_key not in ek


def test_analyze_normalizes_russian_llm_keys_to_english_contract():
    ru_payload = {
        "процессы": ["Регистрация ИБС"], "системы": ["SFA"], "роли": ["Клиентский менеджер"], "интеграции": ["Pega"],
        "kpi": ["Сократить ручные операции"], "бизнес_сущности": ["Договор ИБС"], "документы": ["BRD.pdf"], "термины": ["Автопролонгация"],
        "покрытие": {"документы": True, "системы": True, "процессы": True, "роли": True, "интеграции": True, "bpmn": False, "kpi": True, "sla": False, "ограничения": False},
        "missing_information": [], "рекомендации": []
    }
    agent, _ = _agent_with_response(ru_payload)
    ek = agent.analyze(FakeProject(), _minimal_payload(), previous_context={})["extracted_knowledge"]
    assert ek["processes"] == ["Регистрация ИБС"]
    assert ek["systems"] == ["SFA"]
    assert ek["coverage"]["documents"] is True
    assert ek["coverage"]["roles"] is True
    assert ek["coverage"]["integrations"] is True
    assert ek["coverage"]["constraints"] is False


def test_metadata_only_sources_are_not_marked_as_used_and_create_missing_information():
    agent, _ = _agent_with_response({})
    payload = {
        "context_input": {"short_description": "Автоматизация автопролонгации ИБС"},
        "documents": [{"id": "doc_1", "name": "BRD.pdf"}],
        "links": [{"id": "link_1", "title": "Confluence page", "url": "https://confluence.local/page"}],
    }
    ek = agent.analyze(FakeProject(), payload, previous_context={})["extracted_knowledge"]
    trace = ek["source_trace"]
    doc = next(x for x in trace if x["source_type"] == "document")
    link = next(x for x in trace if x["source_type"] == "link")
    assert doc["source_id"] == "doc_1" and doc["content_level"] == "metadata_only" and doc["used"] is False
    assert link["source_id"] == "link_1" and link["content_level"] == "metadata_only" and link["used"] is False
    assert any("Не извлечён текст документа" in m for m in ek["missing_information"])
    assert any("Не получено содержимое ссылки" in m for m in ek["missing_information"])


def test_document_with_text_content_is_used_with_text_content_level():
    agent, _ = _agent_with_response({})
    payload = {"context_input": {"short_description": "x"}, "documents": [{"id": "doc_text", "name": "BRD.pdf", "text_content": "Описание процесса"}], "links": []}
    trace = agent.analyze(FakeProject(), payload, previous_context={})["extracted_knowledge"]["source_trace"]
    doc = next(x for x in trace if x["source_id"] == "doc_text")
    assert doc["used"] is True
    assert doc["content_level"] == "text_content"
    assert "Использовано содержимое источника" in doc["reason"]


def test_document_with_extracted_text_is_used_with_extracted_text_level():
    agent, _ = _agent_with_response({})
    payload = {"context_input": {"short_description": "x"}, "documents": [{"id": "doc_extracted", "name": "BRD.pdf", "extracted_text": "Извлечённый текст документа."}], "links": []}
    trace = agent.analyze(FakeProject(), payload, previous_context={})["extracted_knowledge"]["source_trace"]
    doc = next(x for x in trace if x["source_id"] == "doc_extracted")
    assert doc["content_level"] == "extracted_text"
    assert doc["used"] is True


def test_link_with_fetched_content_is_used_with_fetched_content_level():
    agent, _ = _agent_with_response({})
    payload = {"context_input": {"short_description": "x"}, "documents": [], "links": [{"id": "link_fetched", "title": "Confluence", "url": "https://confluence.local/page", "fetched_content": "Содержимое страницы"}]}
    trace = agent.analyze(FakeProject(), payload, previous_context={})["extracted_knowledge"]["source_trace"]
    link = next(x for x in trace if x["source_id"] == "link_fetched")
    assert link["content_level"] == "fetched_content"
    assert link["used"] is True


def test_summary_and_chunks_content_levels_are_detected():
    agent, _ = _agent_with_response({})
    payload = {
        "context_input": {"short_description": "x"},
        "documents": [{"id": "doc_summary", "name": "summary.pdf", "summary": "Краткое резюме документа"}],
        "links": [{"id": "link_chunks", "title": "Jira Epic", "url": "https://jira.local/epic", "chunks": [{"text": "Фрагмент 1"}, {"text": "Фрагмент 2"}]}],
    }
    trace = agent.analyze(FakeProject(), payload, previous_context={})["extracted_knowledge"]["source_trace"]
    doc = next(x for x in trace if x["source_id"] == "doc_summary")
    link = next(x for x in trace if x["source_id"] == "link_chunks")
    assert doc["content_level"] == "summary" and doc["used"] is True
    assert link["content_level"] == "chunks" and link["used"] is True


def test_invalid_llm_json_uses_deterministic_fallback():
    agent = ContextIngestionAgent(InvalidJsonLLM())
    result = agent.analyze(FakeProject(), _minimal_payload(), previous_context={})
    ek = result["extracted_knowledge"]
    assert "processes" in ek and "systems" in ek and "coverage" in ek
    assert set(ek["coverage"].keys()) == {"documents", "systems", "processes", "roles", "integrations", "bpmn", "kpi", "sla", "constraints"}
    assert "source_trace" in ek
    assert "missing_information" in ek


def test_coverage_always_contains_full_contract():
    agent, _ = _agent_with_response({"coverage": {"documents": True}})
    coverage = agent.analyze(FakeProject(), _minimal_payload(), previous_context={})["extracted_knowledge"]["coverage"]
    assert set(coverage.keys()) == {"documents", "systems", "processes", "roles", "integrations", "bpmn", "kpi", "sla", "constraints"}


def test_prompt_requests_english_json_keys():
    llm = StaticLLM("{}")
    agent = ContextIngestionAgent(llm)
    agent.analyze(FakeProject(), _minimal_payload(), previous_context={})
    prompt = llm.last_prompt
    assert "JSON keys must be English" in prompt
    assert '"processes"' in prompt
    assert '"business_entities"' in prompt
    assert '"coverage"' in prompt
    assert '"missing_information"' in prompt
    assert '"процессы":[]' not in prompt
    assert '"бизнес_сущности":[]' not in prompt
    assert '"покрытие":{' not in prompt
