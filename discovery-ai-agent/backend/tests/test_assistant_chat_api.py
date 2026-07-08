import sys
from pathlib import Path
import json

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.api import discovery
from app.models.assistant import AssistantToolRun
from app.models.discovery import ArtifactType, Base, DiscoveryProject
from app.models.llm_settings import LLMSettings
from app.repositories import assistant as assistant_repo
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
    assert "problem_statement" in payload["preview"]["changed_fields"]
    assert "pains" in payload["preview"]["changed_fields"]
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


def test_assistant_tool_runs_do_not_store_full_patch_or_retrieved_chunk_text():
    db = _session()
    project = _create_project(db)
    sensitive_chunk = "СЕКРЕТНЫЙ КОРПОРАТИВНЫЙ ФРАГМЕНТ: клиентский процесс и внутренний регламент."
    discovery_repo.upsert_artifact(
        db,
        project.id,
        ArtifactType.CONTEXT,
        "",
        structured_content={
            "uploaded_files": [
                {
                    "id": "doc_1",
                    "name": "internal.md",
                    "text_extraction_status": "completed",
                    "chunks": [{"id": "chunk_1", "text": sensitive_chunk, "order": 0}],
                }
            ],
            "source_trace": [
                {"source_id": "doc_1", "source_type": "document", "source_name": "internal.md", "used": True, "content_level": "chunks"}
            ],
        },
    )

    chat = discovery.assistant_chat(
        project.id,
        discovery.AssistantChatRequest(message="@problem клиентский процесс", artifact_type=None),
        db=db,
    )
    discovery.assistant_apply_patch(
        project.id,
        discovery.AssistantApplyPatchRequest(session_id=chat["session_id"], action_id=chat["action"]["id"]),
        db=db,
    )

    rows = db.query(AssistantToolRun).filter(AssistantToolRun.project_id == project.id).all()
    serialized = json.dumps(
        [{"input": row.input_json, "output": row.output_json, "error": row.error_message} for row in rows],
        ensure_ascii=False,
    )

    assert sensitive_chunk not in serialized
    assert "proposed_patch" not in serialized
    assert '"patch"' not in serialized
    assert "patch_hash" in serialized


def test_assistant_apply_patch_rejects_rejected_or_failed_actions():
    db = _session()
    project = _create_project(db)
    chat = discovery.assistant_chat(
        project.id,
        discovery.AssistantChatRequest(message="Проблема: ручной процесс.", artifact_type=ArtifactType.PROBLEM),
        db=db,
    )
    action = assistant_repo.get_action(db, project.id, chat["session_id"], chat["action"]["id"])
    assistant_repo.update_action(db, action, status="rejected")

    with pytest.raises(HTTPException) as exc:
        discovery.assistant_apply_patch(
            project.id,
            discovery.AssistantApplyPatchRequest(session_id=chat["session_id"], action_id=chat["action"]["id"]),
            db=db,
        )

    assert exc.value.status_code == 400
    assert exc.value.detail["human_message"] == "Patch нельзя применить в текущем статусе."


def test_assistant_apply_patch_rejects_artifact_type_outside_chat_allowlist():
    db = _session()
    project = _create_project(db)
    session = assistant_repo.create_session(db, project.id)
    action = assistant_repo.add_action(
        db,
        project_id=project.id,
        session_id=session.id,
        message_id=None,
        action_type="proposed_patch",
        target_artifact_type=ArtifactType.CONTEXT.value,
        proposed_patch={"content": "AI Chat не должен обновлять context напрямую."},
        preview={"changed_fields": ["content"]},
    )

    with pytest.raises(HTTPException) as exc:
        discovery.assistant_apply_patch(
            project.id,
            discovery.AssistantApplyPatchRequest(session_id=session.id, action_id=action.id),
            db=db,
        )

    assert exc.value.status_code == 403
    assert exc.value.detail["human_message"] == "AI Chat не может применять patch к этому типу артефакта."


def test_assistant_apply_patch_rejects_version_conflict():
    db = _session()
    project = _create_project(db)
    artifact = discovery_repo.upsert_artifact(
        db,
        project.id,
        ArtifactType.PROBLEM,
        "Старая проблема",
        structured_content={"problem_statement": "Старая проблема"},
    )
    session = assistant_repo.create_session(db, project.id)
    action = assistant_repo.add_action(
        db,
        project_id=project.id,
        session_id=session.id,
        message_id=None,
        action_type="proposed_patch",
        target_artifact_type=ArtifactType.PROBLEM.value,
        proposed_patch={"problem_statement": "Новая проблема из AI Chat"},
        preview={"changed_fields": ["problem_statement"]},
        action_metadata={"base_artifact_version": artifact.version},
    )
    discovery_repo.upsert_artifact(
        db,
        project.id,
        ArtifactType.PROBLEM,
        "Пользователь уже изменил проблему",
        structured_content={"problem_statement": "Пользователь уже изменил проблему"},
    )

    with pytest.raises(HTTPException) as exc:
        discovery.assistant_apply_patch(
            project.id,
            discovery.AssistantApplyPatchRequest(session_id=session.id, action_id=action.id),
            db=db,
        )

    assert exc.value.status_code == 409
    assert exc.value.detail["error_code"] == "VERSION_CONFLICT"
    assert exc.value.detail["human_message"] == "Артефакт изменился после preview. Обновите preview и попробуйте снова."


def test_assistant_reject_action_endpoint_marks_proposed_patch_rejected():
    db = _session()
    project = _create_project(db)
    chat = discovery.assistant_chat(
        project.id,
        discovery.AssistantChatRequest(message="Проблема: ручной процесс.", artifact_type=ArtifactType.PROBLEM),
        db=db,
    )

    payload = discovery.assistant_reject_action(
        project.id,
        discovery.AssistantRejectActionRequest(session_id=chat["session_id"], action_id=chat["action"]["id"]),
        db=db,
    )

    assert payload["ok"] is True
    assert payload["action"]["status"] == "rejected"


def test_llm_settings_serializer_does_not_expose_raw_provider_error_details():
    row = LLMSettings(
        provider="openrouter",
        base_url="https://private-provider.example/v1",
        api_key="sk-secret-value",
        model="secret-model",
        last_connection_status="backend_error",
        last_error="HTTP 500 https://private-provider.example/v1 Authorization: Bearer sk-secret-value stack trace",
    )

    payload = discovery._serialize_llm_settings_row(row)

    assert payload["last_error"] == "Детали ошибки скрыты. Проверьте настройки provider и backend logs."
    assert "private-provider" not in payload["last_error"]
    assert "sk-secret-value" not in payload["last_error"]
