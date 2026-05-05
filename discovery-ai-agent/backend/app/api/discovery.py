from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.discovery import ArtifactType
from app.repositories import discovery as repo
from app.schemas.discovery import ArtifactRead, ArtifactWrite, ProjectCreate, ProjectRead, ProjectUpdate

router = APIRouter(prefix="/api", tags=["discovery"])


@router.get("/projects", response_model=list[ProjectRead])
def get_projects(db: Session = Depends(get_db)):
    return repo.list_projects(db)


@router.post("/projects", response_model=ProjectRead)
def create_project(payload: ProjectCreate, db: Session = Depends(get_db)):
    return repo.create_project(db, **payload.model_dump())


@router.get("/projects/{project_id}", response_model=ProjectRead)
def get_project(project_id: UUID, db: Session = Depends(get_db)):
    project = repo.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.patch("/projects/{project_id}", response_model=ProjectRead)
def patch_project(project_id: UUID, payload: ProjectUpdate, db: Session = Depends(get_db)):
    project = repo.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return repo.update_project(db, project, **payload.model_dump(exclude_none=True))


@router.delete("/projects/{project_id}")
def remove_project(project_id: UUID, db: Session = Depends(get_db)):
    project = repo.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    repo.delete_project(db, project)
    return {"ok": True}


@router.get("/projects/{project_id}/artifacts", response_model=list[ArtifactRead])
def get_artifacts(project_id: UUID, db: Session = Depends(get_db)):
    return repo.list_artifacts(db, project_id)


@router.get("/projects/{project_id}/artifacts/{artifact_type}", response_model=ArtifactRead)
def get_artifact(project_id: UUID, artifact_type: ArtifactType, db: Session = Depends(get_db)):
    artifact = repo.get_artifact(db, project_id, artifact_type)
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")
    return artifact


@router.put("/projects/{project_id}/artifacts/{artifact_type}", response_model=ArtifactRead)
def put_artifact(project_id: UUID, artifact_type: ArtifactType, payload: ArtifactWrite, db: Session = Depends(get_db)):
    project = repo.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return repo.upsert_artifact(db, project_id, artifact_type, payload.content)
