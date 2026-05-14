import json
import sys
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.agents.context_ingestion_agent import ContextIngestionAgent
from app.api.discovery import analyze_context, generate_problem
from app.models.discovery import ArtifactType, Base, DiscoveryProject
from app.models.llm_settings import LLMSettings
from app.repositories import discovery as repo


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
    return {
        "context_input": {
            "short_description": "Автоматизация автопролонгации ИБС",
            "product_goal": "Сократить ручные операции",
            "business_domain": "Розничный банк",
            "business_process_owner": "Владелец процесса ИБС",
        },
        "documents": [],
        "links": [],
    }


def _db_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, future=True)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    db.add(
        LLMSettings(
            provider="mock",
            base_url="",
            model="mock",
            api_key=None,
            timeout_seconds=30,
            temperature=0.2,
            is_active=True,
        )
    )
    project = DiscoveryProject(project_name="Автопролонгация ИБС", business_domain="Розничный банк")
    db.add(project)
    db.commit()
    db.refresh(project)
    return db, project


def test_analyze_returns_stable_english_contract_keys():
    llm_payload = {
        "processes": ["Регистрация ИБС"],
        "systems": ["SFA"],
        "roles": ["Клиентский менеджер"],
        "integrations": ["Pega"],
        "kpi": ["Сократить ручные операции на 80%"],
        "business_entities": ["Договор ИБС"],
        "documents": ["BRD.pdf"],
        "terms": ["Автопролонгация"],
        "constraints": ["Без OCR"],
        "coverage": {
            "manual_context": True,
            "documents": True,
            "systems": True,
            "processes": True,
            "roles": True,
            "integrations": True,
            "bpmn": False,
            "kpi": True,
            "sla": False,
            "constraints": True,
        },
        "missing_information": [],
        "recommendations": [],
    }
    agent, _ = _agent_with_response(llm_payload)
    result = agent.analyze(FakeProject(), _minimal_payload(), previous_context={})
    ek = result["extracted_knowledge"]

    expected_keys = {
        "processes",
        "systems",
        "roles",
        "integrations",
        "kpi",
        "business_entities",
        "documents",
        "terms",
        "constraints",
        "coverage",
        "readiness",
        "missing_information",
        "recommendations",
        "source_trace",
        "problem_handoff",
    }
    assert expected_keys.issubset(ek.keys())
    assert set(ek["coverage"].keys()) == {
        "manual_context",
        "documents",
        "systems",
        "processes",
        "roles",
        "integrations",
        "bpmn",
        "kpi",
        "sla",
        "constraints",
    }
    assert set(ek["readiness"].keys()) == {
        "status",
        "score",
        "can_go_to_problem",
        "summary",
        "blocking_reasons",
        "warnings",
        "next_actions",
    }
    for ru_key in ["процессы", "системы", "роли", "интеграции", "бизнес_сущности", "покрытие"]:
        assert ru_key not in ek


def test_metadata_only_sources_are_not_marked_as_used_and_create_missing_information():
    agent, _ = _agent_with_response({})
    payload = {
        "context_input": {"short_description": "Автоматизация автопролонгации ИБС"},
        "documents": [{"id": "doc_1", "name": "BRD.pdf", "text_extraction_status": "unsupported"}],
        "links": [{"id": "link_1", "title": "Confluence page", "url": "https://confluence.local/page"}],
    }
    ek = agent.analyze(FakeProject(), payload, previous_context={})["extracted_knowledge"]
    trace = ek["source_trace"]
    doc = next(x for x in trace if x["source_type"] == "document")
    link = next(x for x in trace if x["source_type"] == "link")

    assert doc["source_id"] == "doc_1"
    assert doc["content_level"] == "metadata_only"
    assert doc["used"] is False
    assert link["source_id"] == "link_1"
    assert link["content_level"] == "metadata_only"
    assert link["used"] is False
    assert any("Не извлечён текст документа" in m for m in ek["missing_information"])
    assert any("Не получено содержимое ссылки" in m for m in ek["missing_information"])


def test_invalid_llm_json_uses_deterministic_fallback_without_inventing_content():
    agent = ContextIngestionAgent(InvalidJsonLLM())
    result = agent.analyze(FakeProject(), {"context_input": {}, "documents": [], "links": []}, previous_context={})
    ek = result["extracted_knowledge"]

    assert ek["processes"] == []
    assert ek["systems"] == []
    assert ek["roles"] == []
    assert ek["integrations"] == []
    assert ek["kpi"] == []
    assert ek["business_entities"] == []
    assert ek["readiness"]["status"] == "blocked"
    assert ek["readiness"]["can_go_to_problem"] is False


def test_readiness_warning_for_manual_context_without_core_facts():
    agent = ContextIngestionAgent(InvalidJsonLLM())
    ek = agent.analyze(FakeProject(), _minimal_payload(), previous_context={})["extracted_knowledge"]

    assert ek["readiness"]["status"] == "warning"
    assert ek["readiness"]["can_go_to_problem"] is True
    assert any("процесс" in x.lower() for x in ek["readiness"]["next_actions"])


def test_readiness_ready_when_core_context_and_usable_source_are_present():
    llm_payload = {
        "processes": ["Автопролонгация ИБС"],
        "systems": ["SFA"],
        "roles": ["Оператор"],
        "integrations": ["API SFA"],
        "kpi": ["Сократить ручные операции на 80%"],
        "constraints": ["Без OCR"],
        "coverage": {
            "manual_context": True,
            "documents": True,
            "systems": True,
            "processes": True,
            "roles": True,
            "integrations": True,
            "kpi": True,
            "constraints": True,
        },
    }
    agent, _ = _agent_with_response(llm_payload)
    payload = {
        **_minimal_payload(),
        "documents": [{"id": "doc_text", "name": "context.txt", "extracted_text": "Процесс Автопролонгация ИБС использует SFA"}],
    }
    ek = agent.analyze(FakeProject(), payload, previous_context={})["extracted_knowledge"]

    assert ek["readiness"]["status"] == "ready"
    assert ek["readiness"]["score"] >= 70
    assert ek["readiness"]["can_go_to_problem"] is True


def test_problem_handoff_contract_is_returned_for_problem_stage():
    llm_payload = {
        "processes": ["Автопролонгация ИБС"],
        "systems": ["SFA IBS"],
        "roles": ["Оператор"],
        "constraints": ["Нет BPMN"],
        "kpi": ["Сократить ручные операции"],
        "problem_handoff": {
            "context_summary": "Контекст описывает автопролонгацию ИБС.",
            "known_processes": ["Автопролонгация ИБС"],
            "known_systems": ["SFA IBS"],
            "known_roles": ["Оператор"],
            "known_integrations": [],
            "known_constraints": ["Нет BPMN"],
            "known_kpi": ["Сократить ручные операции"],
            "evidence": ["context.txt"],
            "open_questions": ["Не описан SLA"],
        },
    }
    agent, _ = _agent_with_response(llm_payload)
    handoff = agent.analyze(FakeProject(), _minimal_payload(), previous_context={})["problem_handoff"]

    assert set(handoff.keys()) == {
        "context_summary",
        "known_processes",
        "known_systems",
        "known_roles",
        "known_integrations",
        "known_constraints",
        "known_kpi",
        "evidence",
        "open_questions",
    }
    assert handoff["known_processes"] == ["Автопролонгация ИБС"]
    assert "Не описан SLA" in handoff["open_questions"]


def test_prompt_forbids_solution_requirements_to_be_and_final_bt():
    llm = StaticLLM("{}")
    agent = ContextIngestionAgent(llm)
    agent.analyze(FakeProject(), _minimal_payload(), previous_context={})
    prompt = llm.last_prompt

    assert "JSON keys must be English" in prompt
    assert "do not generate TO-BE" in prompt
    assert "do not generate solution" in prompt
    assert "do not generate requirements" in prompt
    assert "do not generate final BT" in prompt
    assert '"processes"' in prompt
    assert '"problem_handoff"' in prompt
    assert '"процессы":[]' not in prompt


def test_chunk_dicts_are_compacted_as_text_not_python_dict_repr():
    llm = StaticLLM("{}")
    agent = ContextIngestionAgent(llm)
    payload = {
        "context_input": {"short_description": "x"},
        "documents": [{"id": "doc_chunks", "name": "notes.txt", "chunks": [{"order": 0, "text": "Первый фрагмент"}]}],
        "links": [],
    }
    agent.analyze(FakeProject(), payload, previous_context={})

    assert "Первый фрагмент" in llm.last_prompt
    assert "{'order':" not in llm.last_prompt


def test_context_analyze_endpoint_saves_problem_handoff_and_indexing_status():
    db, project = _db_session()

    response = analyze_context(
        project.id,
        {
            "context_input": {"short_description": "Автоматизация ИБС"},
            "documents": [{"id": "doc_1", "name": "context.txt", "extracted_text": "Процесс ИБС использует SFA"}],
            "links": [],
        },
        db=db,
    )
    artifact = repo.get_artifact(db, project.id, ArtifactType.CONTEXT)

    assert response["ok"] is True
    assert response["indexing_status"] == "completed"
    assert response["readiness"]["status"] in {"warning", "ready"}
    assert artifact.structured_content["indexing_status"] == "completed"
    assert artifact.structured_content["extracted_knowledge"]
    assert artifact.structured_content["source_trace"]
    assert artifact.structured_content["coverage"]
    assert artifact.structured_content["readiness"]
    assert artifact.structured_content["problem_handoff"]
    assert artifact.structured_content["indexed_at"]


def test_problem_generation_saves_context_handoff_trace_and_version():
    db, project = _db_session()
    context = repo.upsert_artifact(
        db,
        project.id,
        ArtifactType.CONTEXT,
        "",
        structured_content={
            "context_input": {"short_description": "Автоматизация ИБС"},
            "problem_handoff": {"context_summary": "Контекст ИБС", "known_processes": ["ИБС"]},
            "source_trace": [{"source_id": "doc_1", "used": True}],
            "readiness": {"status": "warning", "score": 45, "can_go_to_problem": True},
        },
    )

    response = generate_problem(project.id, payload={}, db=db)
    structured = response["structured_content"]

    assert structured["source_context_version"] == context.version
    assert structured["source_trace"] == [{"source_id": "doc_1", "used": True}]
    assert structured["problem_handoff"]["context_summary"] == "Контекст ИБС"
