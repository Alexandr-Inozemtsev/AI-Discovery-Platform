from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.agents.critic_agent import CriticAgent
from app.agents.orchestrator import AgentOrchestrator
from app.llm.factory import create_llm
from app.models.llm_settings import LLMSettings
from app.db.session import get_db
from app.models.discovery import ArtifactType
from app.repositories import discovery as repo
from app.schemas.discovery import ArtifactRead, ArtifactWrite, CompletionResponse, CompletionSection, ProjectCreate, ProjectRead, ProjectUpdate
from app.services.docx_export_service import build_docx
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/api", tags=["discovery"])
orchestrator = None
critic = None

SECTION_META = {
    "CONTEXT": ("Контекст", True), "PROBLEM": ("Проблема", True), "GOAL": ("Цель", True), "BUSINESS_EFFECT": ("Бизнес-эффект", True),
    "AS_IS": ("AS IS", True), "TO_BE": ("TO BE", True), "USE_CASES": ("Use Cases", True), "FUNCTIONAL_REQUIREMENTS": ("Требования", True),
    "RISKS": ("Риски", True), "FINAL_BT": ("Финальный БТ", True), "NON_FUNCTIONAL_REQUIREMENTS": ("Нефункциональные", False), "VALIDATION_REPORT": ("Отчёт проверки", False),
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
    return repo.upsert_artifact(db, project_id, artifact_type, payload.content, payload.structured_content, payload.rich_content_json, payload.rendered_html)

@router.post('/projects/{project_id}/generate/{artifact_type}', response_model=ArtifactRead)
def generate_artifact(project_id: str, artifact_type: ArtifactType, db: Session = Depends(get_db)):
    p = repo.get_project(db, project_id)
    if not p: raise HTTPException(404, 'Проект не найден')
    orchestrator = AgentOrchestrator(create_llm(db))
    agent = orchestrator.get_agent(artifact_type.value)
    if not agent: raise HTTPException(400, 'Генерация для этого типа артефакта не поддерживается')
    content = agent.run(p, {k: v['content'] for k, v in _existing_artifacts_map(db, project_id).items()})
    return repo.upsert_artifact(db, project_id, artifact_type, content, None)

@router.post('/projects/{project_id}/validate', response_model=ArtifactRead)
def validate_project(project_id: str, db: Session = Depends(get_db)):
    p = repo.get_project(db, project_id)
    if not p: raise HTTPException(404, 'Проект не найден')
    critic = CriticAgent(create_llm(db))
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
        text=(a.content or '').strip() if a else ''
        if not a or not text:
            status='not_started'
        elif len(text) < 50:
            status='in_progress'
        else:
            status='completed'
        if req:
            req_total += 1
            if status == 'completed': req_done +=1
            else: missing.append(title)
        sections.append(CompletionSection(artifact_type=ArtifactType(t), title=title, status=status, is_required=req, version=(a.version if a else 0)))
    pct = int((req_done/req_total)*100) if req_total else 0
    return CompletionResponse(completion_percent=pct, sections=sections, required_sections_total=req_total, required_sections_completed=req_done, missing_sections=missing)


@router.get('/projects/{project_id}/export/docx')
def export_docx(project_id: str, db: Session = Depends(get_db)):
    p = repo.get_project(db, project_id)
    if not p: raise HTTPException(404, 'Project not found')
    bio = build_docx(p, repo.list_artifacts(db, project_id))
    return StreamingResponse(bio, media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document', headers={'Content-Disposition': f'attachment; filename=BT_{project_id}.docx'})


@router.get('/settings/llm')
def get_llm_settings(db: Session = Depends(get_db)):
    s = db.query(LLMSettings).order_by(LLMSettings.id.desc()).first()
    if not s:
        return {'provider':'mock','base_url':'','api_key':'','model':'','timeout_seconds':60,'temperature':0.2,'is_active':True}
    key = s.api_key or ''
    masked = key[:3] + '****' + key[-4:] if len(key) > 7 else ('****' if key else '')
    return {'provider':s.provider,'base_url':s.base_url,'api_key':masked,'model':s.model,'timeout_seconds':s.timeout_seconds,'temperature':s.temperature,'is_active':s.is_active}

@router.put('/settings/llm')
def put_llm_settings(payload: dict, db: Session = Depends(get_db)):
    old = db.query(LLMSettings).order_by(LLMSettings.id.desc()).first()
    api_key = payload.get('api_key') if payload.get('api_key') else (old.api_key if old else None)
    s = LLMSettings(provider=payload.get('provider','mock'), base_url=payload.get('base_url'), api_key=api_key, model=payload.get('model'), timeout_seconds=payload.get('timeout_seconds',60), temperature=payload.get('temperature',0.2), is_active=True)
    db.add(s); db.commit(); db.refresh(s)
    return {'ok': True}

@router.post('/settings/llm/test')
def test_llm(db: Session = Depends(get_db)):
    try:
        llm = create_llm(db)
        text = llm.generate('Проверка подключения. Ответь OK.')
        return {'ok': True, 'message': text[:120]}
    except Exception as e:
        raise HTTPException(400, f'Ошибка подключения: {e}')
