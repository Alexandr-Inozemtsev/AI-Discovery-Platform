from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.discovery import ArtifactType, DiscoveryArtifact, DiscoveryProject


def list_projects(db: Session):
    return db.scalars(select(DiscoveryProject).order_by(DiscoveryProject.created_at.desc())).all()


def create_project(db: Session, **kwargs):
    project = DiscoveryProject(**kwargs)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def get_project(db: Session, project_id):
    return db.get(DiscoveryProject, project_id)


def update_project(db: Session, project: DiscoveryProject, **kwargs):
    for key, value in kwargs.items():
        setattr(project, key, value)
    db.commit()
    db.refresh(project)
    return project


def delete_project(db: Session, project: DiscoveryProject):
    db.delete(project)
    db.commit()


def list_artifacts(db: Session, project_id):
    return db.scalars(select(DiscoveryArtifact).where(DiscoveryArtifact.project_id == project_id)).all()


def get_artifact(db: Session, project_id, artifact_type: ArtifactType):
    return db.scalars(
        select(DiscoveryArtifact).where(
            DiscoveryArtifact.project_id == project_id,
            DiscoveryArtifact.artifact_type == artifact_type,
        )
    ).first()


def upsert_artifact(db: Session, project_id, artifact_type: ArtifactType, content: str, structured_content=None, rich_content_json=None, rendered_html=None):
    # Русский комментарий: версия увеличивается на каждом сохранении существующего артефакта.
    artifact = get_artifact(db, project_id, artifact_type)
    if artifact is None:
        artifact = DiscoveryArtifact(project_id=project_id, artifact_type=artifact_type, content=content, structured_content=structured_content, rich_content_json=rich_content_json, rendered_html=rendered_html, version=1)
        db.add(artifact)
    else:
        artifact.content = content
        artifact.structured_content = structured_content
        artifact.rich_content_json = rich_content_json
        artifact.rendered_html = rendered_html
        artifact.version += 1
    db.commit()
    db.refresh(artifact)
    return artifact
