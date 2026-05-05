from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.agents.critic_agent import CriticAgent
from app.agents.orchestrator import AgentOrchestrator
from app.db.session import get_db
from app.models.discovery import ArtifactType
from app.repositories import discovery as repo
from app.schemas.discovery import ArtifactRead, ArtifactWrite, ProjectCreate, ProjectRead, ProjectUpdate

router = APIRouter(prefix="/api", tags=["discovery"])
orchestrator = AgentOrchestrator()
critic = CriticAgent(orchestrator.get_agent("PROBLEM").llm)


def _existing_artifacts_map(db: Session, project_id: str) -> dict[str, str]:
    artifacts = repo.list_artifacts(db, project_id)
    return {a.artifact_type.value: a.content for a in artifacts}


@router.get("/projects", response_model=list[ProjectRead])
def get_projects(db: Session = Depends(get_db)):
    return repo.list_projects(db)


@router.post("/projects", response_model=ProjectRead)
def create_project(payload: ProjectCreate, db: Session = Depends(get_db)):
    return repo.create_project(db, **payload.model_dump())


@router.get("/projects/{project_id}", response_model=ProjectRead)
def get_project(project_id: str, db: Session = Depends(get_db)):
    project = repo.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.patch("/projects/{project_id}", response_model=ProjectRead)
def patch_project(project_id: str, payload: ProjectUpdate, db: Session = Depends(get_db)):
    project = repo.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return repo.update_project(db, project, **payload.model_dump(exclude_none=True))


@router.delete("/projects/{project_id}")
def remove_project(project_id: str, db: Session = Depends(get_db)):
    project = repo.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    repo.delete_project(db, project)
    return {"ok": True}


@router.get("/projects/{project_id}/artifacts", response_model=list[ArtifactRead])
def get_artifacts(project_id: str, db: Session = Depends(get_db)):
    return repo.list_artifacts(db, project_id)


@router.get("/projects/{project_id}/artifacts/{artifact_type}", response_model=ArtifactRead)
def get_artifact(project_id: str, artifact_type: ArtifactType, db: Session = Depends(get_db)):
    artifact = repo.get_artifact(db, project_id, artifact_type)
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")
    return artifact


@router.put("/projects/{project_id}/artifacts/{artifact_type}", response_model=ArtifactRead)
def put_artifact(project_id: str, artifact_type: ArtifactType, payload: ArtifactWrite, db: Session = Depends(get_db)):
    project = repo.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return repo.upsert_artifact(db, project_id, artifact_type, payload.content)


@router.post("/projects/{project_id}/generate/{artifact_type}", response_model=ArtifactRead)
def generate_artifact(project_id: str, artifact_type: ArtifactType, db: Session = Depends(get_db)):
    project = repo.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Проект не найден")
    agent = orchestrator.get_agent(artifact_type.value)
    if not agent:
        raise HTTPException(status_code=400, detail="Генерация для этого типа артефакта не поддерживается")
    content = agent.run(project, _existing_artifacts_map(db, project_id))
    return repo.upsert_artifact(db, project_id, artifact_type, content)


@router.post("/projects/{project_id}/validate", response_model=ArtifactRead)
def validate_project(project_id: str, db: Session = Depends(get_db)):
    project = repo.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Проект не найден")
    # Русский комментарий: отчёт проверки храним отдельным артефактом VALIDATION_REPORT.
    content = critic.run(project, _existing_artifacts_map(db, project_id))
    return repo.upsert_artifact(db, project_id, ArtifactType.VALIDATION_REPORT, content)
