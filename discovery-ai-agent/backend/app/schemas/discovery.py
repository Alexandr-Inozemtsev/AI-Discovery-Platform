from datetime import datetime
from typing import Any

from pydantic import BaseModel

from app.models.discovery import ArtifactType, ProjectStage, ProjectStatus


class ProjectCreate(BaseModel):
    project_name: str
    business_domain: str | None = None
    jira_epic_url: str | None = None


class ProjectUpdate(BaseModel):
    project_name: str | None = None
    business_domain: str | None = None
    jira_epic_url: str | None = None
    status: ProjectStatus | None = None
    current_stage: ProjectStage | None = None


class ProjectRead(BaseModel):
    id: str
    project_name: str
    business_domain: str | None
    status: ProjectStatus
    current_stage: ProjectStage
    jira_epic_url: str | None
    created_at: datetime
    updated_at: datetime
    class Config: from_attributes = True


class ArtifactWrite(BaseModel):
    content: str = ""
    structured_content: dict[str, Any] | None = None


class ArtifactRead(BaseModel):
    id: str
    project_id: str
    artifact_type: ArtifactType
    content: str
    structured_content: dict[str, Any] | None
    version: int
    created_at: datetime
    updated_at: datetime
    class Config: from_attributes = True


class CompletionSection(BaseModel):
    artifact_type: ArtifactType
    title: str
    is_required: bool
    is_completed: bool
    completion_notes: str


class CompletionResponse(BaseModel):
    completion_percent: int
    required_sections_total: int
    required_sections_completed: int
    missing_sections: list[str]
    sections: list[CompletionSection]
