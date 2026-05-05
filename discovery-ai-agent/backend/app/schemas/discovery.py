from datetime import datetime
from uuid import UUID

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
    id: UUID
    project_name: str
    business_domain: str | None
    status: ProjectStatus
    current_stage: ProjectStage
    jira_epic_url: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ArtifactWrite(BaseModel):
    content: str


class ArtifactRead(BaseModel):
    id: UUID
    project_id: UUID
    artifact_type: ArtifactType
    content: str
    version: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
