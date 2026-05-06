"""create discovery tables

Revision ID: 0001
Revises: 
Create Date: 2026-05-05 00:00:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    project_status = sa.Enum("DRAFT", "IN_PROGRESS", "BT_READY", "APPROVED", name="projectstatus")
    project_stage = sa.Enum(
        "CONTEXT", "PROBLEM", "GOAL", "BUSINESS_EFFECT", "AS_IS", "TO_BE", "USE_CASES", "REQUIREMENTS", "RISKS", "FINAL_BT", name="projectstage"
    )
    artifact_type = sa.Enum(
        "CONTEXT", "PROBLEM", "GOAL", "BUSINESS_EFFECT", "AS_IS", "TO_BE", "USE_CASES", "FUNCTIONAL_REQUIREMENTS", "NON_FUNCTIONAL_REQUIREMENTS", "RISKS", "GLOSSARY", "FINAL_BT", name="artifacttype"
    )

    project_status.create(op.get_bind(), checkfirst=True)
    project_stage.create(op.get_bind(), checkfirst=True)
    artifact_type.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "discovery_projects",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("project_name", sa.String(length=255), nullable=False),
        sa.Column("business_domain", sa.String(length=255), nullable=True),
        sa.Column("status", project_status, nullable=False),
        sa.Column("current_stage", project_stage, nullable=False),
        sa.Column("jira_epic_url", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "discovery_artifacts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("discovery_projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("artifact_type", artifact_type, nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("discovery_artifacts")
    op.drop_table("discovery_projects")
    sa.Enum(name="artifacttype").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="projectstage").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="projectstatus").drop(op.get_bind(), checkfirst=True)
