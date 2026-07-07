import uuid
from datetime import datetime

from sqlalchemy import JSON, CheckConstraint, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.discovery import Base


class AssistantSession(Base):
    __tablename__ = "assistant_sessions"
    __table_args__ = (
        CheckConstraint("status IN ('active', 'archived')", name="ck_assistant_sessions_status"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("discovery_projects.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), default="AI Discovery Chat", nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="active", nullable=False)
    session_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    messages: Mapped[list["AssistantMessage"]] = relationship(back_populates="session", cascade="all, delete-orphan")
    actions: Mapped[list["AssistantAction"]] = relationship(back_populates="session", cascade="all, delete-orphan")
    tool_runs: Mapped[list["AssistantToolRun"]] = relationship(back_populates="session", cascade="all, delete-orphan")


class AssistantMessage(Base):
    __tablename__ = "assistant_messages"
    __table_args__ = (
        CheckConstraint("role IN ('user', 'assistant', 'system')", name="ck_assistant_messages_role"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("discovery_projects.id", ondelete="CASCADE"), nullable=False)
    session_id: Mapped[str] = mapped_column(String(36), ForeignKey("assistant_sessions.id", ondelete="CASCADE"), nullable=False)
    role: Mapped[str] = mapped_column(String(32), nullable=False)
    content: Mapped[str] = mapped_column(Text, default="", nullable=False)
    payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    session: Mapped[AssistantSession] = relationship(back_populates="messages")


class AssistantAction(Base):
    __tablename__ = "assistant_actions"
    __table_args__ = (
        CheckConstraint("status IN ('proposed', 'previewed', 'applied', 'rejected', 'failed')", name="ck_assistant_actions_status"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("discovery_projects.id", ondelete="CASCADE"), nullable=False)
    session_id: Mapped[str] = mapped_column(String(36), ForeignKey("assistant_sessions.id", ondelete="CASCADE"), nullable=False)
    message_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("assistant_messages.id", ondelete="SET NULL"), nullable=True)
    action_type: Mapped[str] = mapped_column(String(64), nullable=False)
    target_artifact_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="proposed", nullable=False)
    proposed_patch: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    preview: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    result: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    action_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    session: Mapped[AssistantSession] = relationship(back_populates="actions")
    tool_runs: Mapped[list["AssistantToolRun"]] = relationship(back_populates="action", cascade="all, delete-orphan")


class AssistantToolRun(Base):
    __tablename__ = "assistant_tool_runs"
    __table_args__ = (
        CheckConstraint("status IN ('success', 'failed', 'blocked')", name="ck_assistant_tool_runs_status"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("discovery_projects.id", ondelete="CASCADE"), nullable=False)
    session_id: Mapped[str] = mapped_column(String(36), ForeignKey("assistant_sessions.id", ondelete="CASCADE"), nullable=False)
    action_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("assistant_actions.id", ondelete="SET NULL"), nullable=True)
    tool_name: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    input_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    output_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    session: Mapped[AssistantSession] = relationship(back_populates="tool_runs")
    action: Mapped[AssistantAction | None] = relationship(back_populates="tool_runs")
