from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.models.discovery import ArtifactType


class ProposedPatch(BaseModel):
    artifact_type: ArtifactType
    patch: dict[str, Any] = Field(default_factory=dict)
    reason: str = ""
    source: str = "ai_discovery_chat"


class AssistantChatRequest(BaseModel):
    message: str
    session_id: str | None = None
    artifact_type: ArtifactType | None = None
    context: dict[str, Any] | None = None


class AssistantApplyPatchRequest(BaseModel):
    session_id: str
    action_id: str


class AssistantSessionRead(BaseModel):
    id: str
    project_id: str
    title: str
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AssistantMessageRead(BaseModel):
    id: str
    project_id: str
    session_id: str
    role: str
    content: str
    payload: dict[str, Any] | None
    created_at: datetime

    class Config:
        from_attributes = True
