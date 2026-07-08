import sys
from pathlib import Path

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.api import discovery
from app.models.discovery import ArtifactType, Base, DiscoveryProject
from app.repositories import discovery as discovery_repo


def _session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, future=True)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()


def _create_project(db):
    project = DiscoveryProject(project_name="Assistant Chat", business_domain="Банк")
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def test_assistant_chat_creates_session_messages_and_proposed_patch_without_applying_artifact():
    db = _session()
    project = _create_project(db)

    payload = discovery.assistant_chat(
        project.id,
        discovery.AssistantChatRequest(
            message="Сформулируй проблему: слишком долго готовим Discovery.",
            artifact_type=ArtifactType.PROBLEM,
        ),
        db=db,
    )

    assert payload["ok"] is True
    assert payload["session_id"]
    assert payload["assistant_message"]["role"] == "assistant"
    assert payload["action"]["status"] == "proposed"
    assert payload["action"]["target_artifact_type"] == "PROBLEM"
    assert payload["action"]["proposed_patch"]["problem_statement"]
    assert payload["preview"]["changed_fields"] == ["problem_statement"]
    assert discovery_repo.get_artifact(db, project.id, ArtifactType.PROBLEM) is None

    sessions = discovery.get_assistant_sessions(project.id, db=db)
    assert sessions["ok"] is True
    assert len(sessions["sessions"]) == 1

    messages = discovery.get_assistant_session_messages(project.id, payload["session_id"], db=db)
    assert messages["ok"] is True
    assert [message["role"] for message in messages["messages"]] == ["user", "assistant"]


def test_assistant_apply_patch_requires_separate_call_and_updates_artifact_version():
    db = _session()
    project = _create_project(db)
    chat = discovery.assistant_chat(
        project.id,
        discovery.AssistantChatRequest(
            message="Проблема: ручная подготовка БТ занимает неделю.",
            artifact_type=ArtifactType.PROBLEM,
        ),
        db=db,
    )

    payload = discovery.assistant_apply_patch(
        project.id,
        discovery.AssistantApplyPatchRequest(session_id=chat["session_id"], action_id=chat["action"]["id"]),
        db=db,
    )

    assert payload["ok"] is True
    assert payload["artifact"]["artifact_type"] == ArtifactType.PROBLEM
    assert payload["artifact"]["version"] == 1
    assert payload["action"]["status"] == "applied"

    artifact = discovery_repo.get_artifact(db, project.id, ArtifactType.PROBLEM)
    assert artifact is not None
    assert artifact.structured_content["problem_statement"]


def test_assistant_chat_unknown_project_returns_error_envelope():
    db = _session()

    with pytest.raises(HTTPException) as exc:
        discovery.assistant_chat(
            "missing",
            discovery.AssistantChatRequest(message="Что дальше?", artifact_type=ArtifactType.PROBLEM),
            db=db,
        )

    assert exc.value.status_code == 404
    payload = exc.value.detail
    assert payload["ok"] is False
    assert payload["error_code"] == "PROJECT_NOT_FOUND"
    assert payload["human_message"] == "Проект не найден."


def test_assistant_chat_uses_context_retrieval_and_propagates_evidence():
    db = _session()
    project = _create_project(db)
    discovery_repo.upsert_artifact(
        db,
        project.id,
        ArtifactType.CONTEXT,
        "",
        structured_content={
            "uploaded_files": [
                {
                    "id": "doc_1",
                    "name": "context.md",
                    "text_extraction_status": "completed",
                    "chunks": [
                        {"id": "chunk_1", "text": "Клиенты жалуются на задержки пролонгации ИБС.", "order": 0}
                    ],
                },
                {"id": "doc_meta", "name": "scan.pdf", "text_extraction_status": "not_available"},
            ],
            "source_trace": [
                {"source_id": "doc_1", "source_type": "document", "source_name": "context.md", "used": True, "content_level": "chunks"},
                {"source_id": "doc_meta", "source_type": "document", "source_name": "scan.pdf", "used": False, "content_level": "metadata_only"},
            ],
        },
    )

    payload = discovery.assistant_chat(
        project.id,
        discovery.AssistantChatRequest(
            message="@problem сформулируй проблему задержки пролонгации",
        ),
        db=db,
    )

    metadata = payload["action"]["metadata"]
    preview = payload["action"]["preview"]

    assert payload["action"]["target_artifact_type"] == "PROBLEM"
    assert metadata["retrieval"]["chunks"][0]["source_id"] == "doc_1"
    assert metadata["evidence"][0]["chunk_id"] == "chunk_1"
    assert "doc_meta" not in {row.get("source_id") for row in metadata["evidence"]}
    assert preview["evidence_count"] == 1
