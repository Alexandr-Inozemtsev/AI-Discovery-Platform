import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.assistant.chat_context_assembler import ChatContextAssembler
from app.assistant.intent_router import IntentRouter
from app.models.discovery import ArtifactType
from app.rag.simple_retriever import RetrievalQuery, SimpleRetriever


def _context_artifact():
    return {
        "context_input": {
            "short_description": "Автоматизация пролонгации ИБС",
            "product_goal": "Сократить ручные операции",
            "business_domain": "Банковские продукты",
        },
        "uploaded_files": [
            {
                "id": "doc_1",
                "name": "process.md",
                "text_extraction_status": "completed",
                "chunks": [
                    {"id": "c1", "text": "Оператор вручную проверяет договор ИБС и продлевает сейф.", "order": 0},
                    {"id": "c2", "text": "Клиенты жалуются на задержки пролонгации и повторные визиты.", "order": 1},
                ],
            },
            {
                "id": "doc_meta",
                "name": "scan.pdf",
                "text_extraction_status": "not_available",
            },
        ],
        "source_trace": [
            {"source_id": "doc_1", "source_type": "document", "source_name": "process.md", "used": True, "content_level": "chunks"},
            {"source_id": "doc_meta", "source_type": "document", "source_name": "scan.pdf", "used": False, "content_level": "metadata_only"},
        ],
    }


def test_simple_retriever_returns_relevant_chunks_and_excludes_metadata_only_sources():
    result = SimpleRetriever().retrieve(
        RetrievalQuery(
            project_id="project_1",
            query="проблема задержки пролонгации клиентов",
            artifact_type="PROBLEM",
            context_artifact=_context_artifact(),
            top_k=3,
            max_chars=500,
        )
    )

    assert result.ok is True
    assert result.chunks
    assert result.chunks[0].chunk_id == "c2"
    assert {chunk.source_id for chunk in result.chunks} == {"doc_1"}
    assert any("metadata-only" in warning for warning in result.warnings)
    used_trace = [row for row in result.source_trace if row.get("used")]
    assert used_trace[0]["chunk_id"] == "c2"


def test_simple_retriever_respects_context_budget_and_marks_truncated_chunks():
    context = _context_artifact()
    context["uploaded_files"][0]["chunks"][0]["text"] = "ручная операция " * 100

    result = SimpleRetriever().retrieve(
        RetrievalQuery(
            project_id="project_1",
            query="ручная операция",
            artifact_type="PROBLEM",
            context_artifact=context,
            top_k=2,
            max_chars=80,
        )
    )

    assert sum(len(chunk.text) for chunk in result.chunks) <= 80
    assert result.chunks[0].metadata["truncated"] is True
    assert any("budget" in warning for warning in result.warnings)


def test_chat_context_assembler_builds_budgeted_context_with_evidence_and_open_questions():
    retrieval = SimpleRetriever().retrieve(
        RetrievalQuery(
            project_id="project_1",
            query="проблема пролонгации",
            artifact_type="PROBLEM",
            context_artifact=_context_artifact(),
            top_k=2,
            max_chars=400,
        )
    )

    assembled = ChatContextAssembler(max_chars=700).assemble(
        project=SimpleNamespace(id="project_1", project_name="ИБС", business_domain="Банк"),
        artifact_type=ArtifactType.PROBLEM,
        message="@problem сформулируй проблему",
        context_artifact=_context_artifact(),
        artifacts={"GOAL": {"content": "Сократить ручные операции", "version": 1}},
        retrieval_result=retrieval,
    )

    assert assembled["token_budget"]["max_chars"] == 700
    assert len(assembled["prompt_context"]) <= 700
    assert assembled["evidence"]
    assert assembled["retrieved_chunks"][0]["source_id"] == "doc_1"
    assert "Полный корпус документов не передаётся" in assembled["data_policy"]


def test_chat_context_assembler_marks_missing_evidence_as_assumption_and_open_question():
    retrieval = SimpleRetriever().retrieve(
        RetrievalQuery(
            project_id="project_1",
            query="регуляторные ограничения",
            artifact_type="GOAL",
            context_artifact={"uploaded_files": [{"id": "meta", "name": "scan.pdf"}]},
            top_k=2,
            max_chars=300,
        )
    )

    assembled = ChatContextAssembler(max_chars=600).assemble(
        project=SimpleNamespace(id="project_1", project_name="ИБС", business_domain="Банк"),
        artifact_type=ArtifactType.GOAL,
        message="@goal предложи KPI",
        context_artifact={},
        artifacts={},
        retrieval_result=retrieval,
    )

    assert assembled["evidence"] == []
    assert assembled["assumptions"]
    assert assembled["open_questions"]
    assert "нет подтверждённых evidence" in assembled["open_questions"][0].lower()


def test_intent_router_routes_chat_commands_to_prompt_templates():
    router = IntentRouter()

    assert router.route("@context найди gaps").target_artifact_type == ArtifactType.CONTEXT
    assert router.route("@problem сформулируй проблему").target_artifact_type == ArtifactType.PROBLEM
    assert router.route("@goal предложи цель").target_artifact_type == ArtifactType.GOAL
    assert router.route("@business-effect оцени эффект").target_artifact_type == ArtifactType.BUSINESS_EFFECT
    assert router.route("@use-cases создай сценарии").target_artifact_type == ArtifactType.USE_CASES
    assert router.route("@requirements добавь требования").target_artifact_type == ArtifactType.FUNCTIONAL_REQUIREMENTS
    assert router.route("@critic проверь качество").intent_type == "validate_workflow"
    assert router.route("@export подготовь DOCX").intent_type == "export_document"
