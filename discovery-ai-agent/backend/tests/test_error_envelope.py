import json
import sys
from pathlib import Path

import pytest
from fastapi import HTTPException
from fastapi.exceptions import RequestValidationError
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.api import discovery
from app.models.discovery import ArtifactType, Base, DiscoveryProject
from app.models.llm_settings import LLMSettings
from app.repositories import discovery as repo


def _session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, future=True)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()


def _add_llm_settings(db, provider="mock", api_key=None, status=None):
    db.add(
        LLMSettings(
            provider=provider,
            base_url="https://private-llm.example.internal/api/v1",
            model="test-model",
            api_key=api_key,
            timeout_seconds=30,
            temperature=0.2,
            is_active=True,
            last_connection_status=status,
        )
    )
    db.commit()


def _create_project(db):
    project = DiscoveryProject(project_name="Тестовый проект", business_domain="Банк")
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def _assert_error_envelope(payload, code):
    assert payload["ok"] is False
    assert payload["error_code"] == code
    assert payload["human_message"]
    assert isinstance(payload["details"], dict)
    assert "trace_id" in payload


def _raised_detail(call):
    with pytest.raises(HTTPException) as exc:
        call()
    return exc.value.status_code, exc.value.detail


def test_project_not_found_raises_error_envelope():
    db = _session()

    status, payload = _raised_detail(lambda: discovery.get_project("missing", db))

    assert status == 404
    _assert_error_envelope(payload, "PROJECT_NOT_FOUND")
    assert payload["human_message"] == "Проект не найден."


def test_artifact_not_found_raises_error_envelope():
    db = _session()
    project = _create_project(db)

    status, payload = _raised_detail(lambda: discovery.get_artifact(project.id, ArtifactType.PROBLEM, db))

    assert status == 404
    _assert_error_envelope(payload, "ARTIFACT_NOT_FOUND")


def test_llm_not_ready_raises_error_envelope():
    db = _session()
    project = _create_project(db)
    _add_llm_settings(db, provider="openrouter", api_key=None, status="not_configured")

    status, payload = _raised_detail(lambda: discovery.generate_artifact(project.id, ArtifactType.PROBLEM, db))

    assert status == 400
    _assert_error_envelope(payload, "LLM_NOT_READY")
    assert payload["details"]["ready_for_generation"] is False


def test_unsupported_artifact_generation_raises_error_envelope():
    db = _session()
    project = _create_project(db)
    _add_llm_settings(db)

    status, payload = _raised_detail(lambda: discovery.generate_artifact(project.id, ArtifactType.GLOSSARY, db))

    assert status == 400
    _assert_error_envelope(payload, "UNSUPPORTED_ARTIFACT_TYPE")


@pytest.mark.anyio
async def test_validation_handler_returns_error_envelope():
    from app.api.error_handlers import validation_exception_handler

    exc = RequestValidationError(
        [
            {
                "type": "enum",
                "loc": ("path", "artifact_type"),
                "msg": "Input should be a valid enum",
                "input": "NOT_A_TYPE",
            }
        ]
    )

    response = await validation_exception_handler(None, exc)
    payload = json.loads(response.body.decode("utf-8"))

    assert response.status_code == 422
    _assert_error_envelope(payload, "VALIDATION_ERROR")


def test_provider_error_details_are_sanitized(monkeypatch):
    class LeakingLLM:
        provider = "openrouter"
        model = "test-model"

        def generate(self, prompt):
            raise RuntimeError(
                "401 Authorization: Bearer sk-test-placeholder-token at "
                "https://private-llm.example.internal/api/v1/chat/completions"
            )

    db = _session()
    project = _create_project(db)
    _add_llm_settings(db, api_key="sk-test-placeholder-token")
    repo.upsert_artifact(
        db,
        project.id,
        ArtifactType.CONTEXT,
        "Контекст проекта",
        structured_content={"context_input": {"short_description": "Описание"}},
    )
    repo.upsert_artifact(db, project.id, ArtifactType.PROBLEM, "Проблема", structured_content={})
    monkeypatch.setattr("app.api.discovery.create_llm", lambda db: LeakingLLM())

    status, payload = _raised_detail(lambda: discovery.generate_goal(project.id, db))

    assert status == 400
    _assert_error_envelope(payload, "LLM_UNAUTHORIZED")
    raw = str(payload)
    assert "sk-test-placeholder-token" not in raw
    assert "Bearer" not in raw
    assert "private-llm.example.internal" not in raw
