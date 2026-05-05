from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.agents.critic_agent import CriticAgent
from app.agents.orchestrator import AgentOrchestrator
from app.db.session import get_db
from app.models.discovery import ArtifactType
from app.repositories import discovery as repo
from app.schemas.discovery import ArtifactRead, ArtifactWrite, CompletionResponse, CompletionSection, ProjectCreate, ProjectRead, ProjectUpdate

router = APIRouter(prefix="/api", tags=["discovery"])
orchestrator = AgentOrchestrator()
critic = CriticAgent(orchestrator.get_agent("PROBLEM").llm)

SECTION_META = {
    "CONTEXT": ("Контекст", True), "PROBLEM": ("Проблема", True), "GOAL": ("Цель", True), "BUSINESS_EFFECT": ("Бизнес-эффект", True),
    "AS_IS": ("AS IS", True), "TO_BE": ("TO BE", True), "USE_CASES": ("Use Cases", True), "FUNCTIONAL_REQUIREMENTS": ("Требования", True),
    "RISKS": ("Риски", True), "FINAL_BT": ("Финальный БТ", False), "NON_FUNCTIONAL_REQUIREMENTS": ("Нефункциональные", False), "VALIDATION_REPORT": ("Отчёт проверки", False),
}

def _has_values(val):
    if val is None: return False
    if isinstance(val, str): return bool(val.strip())
    if isinstance(val, list): return any(_has_values(v) for v in val)
    if isinstance(val, dict): return any(_has_values(v) for v in val.values())
    return True

def _existing_artifacts_map(db: Session, project_id: str):
    artifacts = repo.list_artifacts(db, project_id)
    return {a.artifact_type.value: {"content": a.content, "structured_content": a.structured_content} for a in artifacts}

@router.get('/projects', response_model=list[ProjectRead])
def get_projects(db: Session = Depends(get_db)): return repo.list_projects(db)
@router.post('/projects', response_model=ProjectRead)
def create_project(payload: ProjectCreate, db: Session = Depends(get_db)): return repo.create_project(db, **payload.model_dump())
@router.get('/projects/{project_id}', response_model=ProjectRead)
def get_project(project_id: str, db: Session = Depends(get_db)):
    p = repo.get_project(db, project_id)
    if not p: raise HTTPException(404, 'Project not found')
    return p
@router.patch('/projects/{project_id}', response_model=ProjectRead)
def patch_project(project_id: str, payload: ProjectUpdate, db: Session = Depends(get_db)):
    p = repo.get_project(db, project_id)
    if not p: raise HTTPException(404, 'Project not found')
    return repo.update_project(db, p, **payload.model_dump(exclude_none=True))
@router.delete('/projects/{project_id}')
def remove_project(project_id: str, db: Session = Depends(get_db)):
    p = repo.get_project(db, project_id)
    if not p: raise HTTPException(404, 'Project not found')
    repo.delete_project(db, p); return {'ok': True}
@router.get('/projects/{project_id}/artifacts', response_model=list[ArtifactRead])
def get_artifacts(project_id: str, db: Session = Depends(get_db)): return repo.list_artifacts(db, project_id)
@router.get('/projects/{project_id}/artifacts/{artifact_type}', response_model=ArtifactRead)
def get_artifact(project_id: str, artifact_type: ArtifactType, db: Session = Depends(get_db)):
    a = repo.get_artifact(db, project_id, artifact_type)
    if not a: raise HTTPException(404, 'Artifact not found')
    return a
@router.put('/projects/{project_id}/artifacts/{artifact_type}', response_model=ArtifactRead)
def put_artifact(project_id: str, artifact_type: ArtifactType, payload: ArtifactWrite, db: Session = Depends(get_db)):
    p = repo.get_project(db, project_id)
    if not p: raise HTTPException(404, 'Project not found')
    return repo.upsert_artifact(db, project_id, artifact_type, payload.content, payload.structured_content)

@router.post('/projects/{project_id}/generate/{artifact_type}', response_model=ArtifactRead)
def generate_artifact(project_id: str, artifact_type: ArtifactType, db: Session = Depends(get_db)):
    p = repo.get_project(db, project_id)
    if not p: raise HTTPException(404, 'Проект не найден')
    agent = orchestrator.get_agent(artifact_type.value)
    if not agent: raise HTTPException(400, 'Генерация для этого типа артефакта не поддерживается')
    content = agent.run(p, {k: v['content'] for k, v in _existing_artifacts_map(db, project_id).items()})
    return repo.upsert_artifact(db, project_id, artifact_type, content, None)

@router.post('/projects/{project_id}/validate', response_model=ArtifactRead)
def validate_project(project_id: str, db: Session = Depends(get_db)):
    p = repo.get_project(db, project_id)
    if not p: raise HTTPException(404, 'Проект не найден')
    content = critic.run(p, {k: v['content'] for k, v in _existing_artifacts_map(db, project_id).items()})
    return repo.upsert_artifact(db, project_id, ArtifactType.VALIDATION_REPORT, content, None)

@router.get('/projects/{project_id}/completion', response_model=CompletionResponse)
def completion(project_id: str, db: Session = Depends(get_db)):
    p = repo.get_project(db, project_id)
    if not p: raise HTTPException(404, 'Project not found')
    art = {a.artifact_type.value: a for a in repo.list_artifacts(db, project_id)}
    sections=[]; req_total=0; req_done=0; missing=[]
    for t,(title,req) in SECTION_META.items():
        a=art.get(t)
        done=bool(a and (_has_values(a.content) or _has_values(a.structured_content)))
        if req:
            req_total += 1
            if done: req_done +=1
            else: missing.append(title)
        sections.append(CompletionSection(artifact_type=ArtifactType(t), title=title, is_required=req, is_completed=done, completion_notes='Заполнено' if done else 'Нужно заполнить'))
    pct = int((req_done/req_total)*100) if req_total else 0
    return CompletionResponse(completion_percent=pct, required_sections_total=req_total, required_sections_completed=req_done, missing_sections=missing, sections=sections)
