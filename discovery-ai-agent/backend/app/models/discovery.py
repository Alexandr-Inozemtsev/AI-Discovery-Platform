import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class ProjectStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    IN_PROGRESS = "IN_PROGRESS"
    BT_READY = "BT_READY"
    APPROVED = "APPROVED"


class ProjectStage(str, enum.Enum):
    CONTEXT = "CONTEXT"
    PROBLEM = "PROBLEM"
    GOAL = "GOAL"
    BUSINESS_EFFECT = "BUSINESS_EFFECT"
    AS_IS = "AS_IS"
    TO_BE = "TO_BE"
    USE_CASES = "USE_CASES"
    REQUIREMENTS = "REQUIREMENTS"
    RISKS = "RISKS"
    FINAL_BT = "FINAL_BT"


class ArtifactType(str, enum.Enum):
    CONTEXT = "CONTEXT"
    PROBLEM = "PROBLEM"
    GOAL = "GOAL"
    BUSINESS_EFFECT = "BUSINESS_EFFECT"
    AS_IS = "AS_IS"
    TO_BE = "TO_BE"
    USE_CASES = "USE_CASES"
    FUNCTIONAL_REQUIREMENTS = "FUNCTIONAL_REQUIREMENTS"
    NON_FUNCTIONAL_REQUIREMENTS = "NON_FUNCTIONAL_REQUIREMENTS"
    RISKS = "RISKS"
    GLOSSARY = "GLOSSARY"
    FINAL_BT = "FINAL_BT"


class DiscoveryProject(Base):
    __tablename__ = "discovery_projects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_name: Mapped[str] = mapped_column(String(255), nullable=False)
    business_domain: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[ProjectStatus] = mapped_column(Enum(ProjectStatus), default=ProjectStatus.DRAFT, nullable=False)
    current_stage: Mapped[ProjectStage] = mapped_column(Enum(ProjectStage), default=ProjectStage.CONTEXT, nullable=False)
    jira_epic_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    artifacts: Mapped[list["DiscoveryArtifact"]] = relationship(back_populates="project", cascade="all, delete-orphan")


class DiscoveryArtifact(Base):
    __tablename__ = "discovery_artifacts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("discovery_projects.id", ondelete="CASCADE"), nullable=False)
    artifact_type: Mapped[ArtifactType] = mapped_column(Enum(ArtifactType), nullable=False)
    content: Mapped[str] = mapped_column(Text, default="", nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    project: Mapped[DiscoveryProject] = relationship(back_populates="artifacts")
