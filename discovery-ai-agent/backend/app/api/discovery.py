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
import json
from urllib import request, error
import time
import re

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


def _json_from_llm_response(raw: str) -> dict:
    txt = (raw or '').strip()
    if not txt:
        return {}
    try:
        return json.loads(txt)
    except Exception:
        m = re.search(r"\{[\s\S]*\}", txt)
        if not m:
            return {}
        return json.loads(m.group(0))

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


@router.post('/projects/{project_id}/context/analyze')
def analyze_context(project_id: str, payload: dict, db: Session = Depends(get_db)):
    p = repo.get_project(db, project_id)
    if not p:
        raise HTTPException(404, 'Проект не найден')
    context_input = payload.get('context_input') or {}
    existing = repo.get_artifact(db, project_id, ArtifactType.CONTEXT)
    prompt = (
        'Ты senior BA assistant. Верни ТОЛЬКО JSON без markdown. '
        'Структура: {"summary":"","business_context":"","problem_statement":"","stakeholders":[],"systems":[],"processes":[],"risks":[],"questions":[],"recommendations":[],"hypothesis":"","completeness_score":0,"missing":[],"detected_entities":{}}. '
        f'Project: {p.project_name}. Context input: {json.dumps(context_input, ensure_ascii=False)}'
    )
    llm = create_llm(db)
    raw = llm.generate(prompt)
    data = _json_from_llm_response(raw)
    if not data:
        raise HTTPException(400, 'LLM вернул некорректный JSON')
    history = (existing.structured_content or {}).get('analysis_history', []) if existing else []
    history.append({'created_at': str(time.time()), 'analysis': data})
    structured = {
        'context_input': context_input,
        'ai_analysis': data,
        'analysis_history': history[-20:],
    }
    content = data.get('summary') or (existing.content if existing else '')
    repo.upsert_artifact(db, project_id, ArtifactType.CONTEXT, content, structured_content=structured)
    return {'ok': True, 'analysis': data, 'history_count': len(history)}

@router.post('/projects/{project_id}/generate/{artifact_type}', response_model=ArtifactRead)
def generate_artifact(project_id: str, artifact_type: ArtifactType, db: Session = Depends(get_db)):
    p = repo.get_project(db, project_id)
    if not p: raise HTTPException(404, 'Проект не найден')
    orchestrator = AgentOrchestrator(create_llm(db))
    agent = orchestrator.get_agent(artifact_type.value)
    if not agent: raise HTTPException(400, 'Генерация для этого типа артефакта не поддерживается')
    try:
        content = agent.run(p, {k: v['content'] for k, v in _existing_artifacts_map(db, project_id).items()})
    except Exception as e:
        if 'openrouter' in str(e).lower() or '401' in str(e) or 'timeout' in str(e).lower():
            raise HTTPException(400, 'OpenRouter недоступен. Проверьте API key, модель и интернет-соединение.')
        raise
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
        return {'provider':'mock','base_url':'https://openrouter.ai/api/v1','api_key':'','model':'deepseek/deepseek-chat-v3-0324:free','timeout_seconds':120,'temperature':0.2,'is_active':True}
    key = s.api_key or ''
    masked = ('********' + key[-4:]) if key else ''
    history = db.query(LLMSettings).filter(LLMSettings.last_error.isnot(None)).order_by(LLMSettings.id.desc()).limit(5).all()
    return {'provider':s.provider,'base_url':s.base_url,'api_key':masked,'model':s.model,'timeout_seconds':s.timeout_seconds,'temperature':s.temperature,'is_active':s.is_active,'last_connection_status':s.last_connection_status,'last_latency_ms':s.last_latency_ms,'last_error':s.last_error,'last_actual_model':s.last_actual_model,'key_tail':(key[-4:] if key else 'none'),'error_history':[{'time':str(x.updated_at),'error':x.last_error} for x in history]}

@router.put('/settings/llm')
def put_llm_settings(payload: dict, db: Session = Depends(get_db)):
    old = db.query(LLMSettings).order_by(LLMSettings.id.desc()).first()
    incoming = payload.get('api_key')
    api_key = old.api_key if old else None
    if incoming and not str(incoming).startswith('********') and not str(incoming).strip()=='':
        api_key = incoming
    s = LLMSettings(provider=payload.get('provider','mock'), base_url=payload.get('base_url'), api_key=api_key, model=payload.get('model'), timeout_seconds=payload.get('timeout_seconds',60), temperature=payload.get('temperature',0.2), is_active=True, last_connection_status=(old.last_connection_status if old else None), last_latency_ms=(old.last_latency_ms if old else None), last_error=(old.last_error if old else None), last_actual_model=(old.last_actual_model if old else None))
    db.add(s); db.commit(); db.refresh(s)
    return {'ok': True}

@router.post('/settings/llm/test')
def test_llm(payload: dict | None = None, db: Session = Depends(get_db)):
    saved = db.query(LLMSettings).order_by(LLMSettings.id.desc()).first()
    src = payload or {}
    provider = (src.get('provider') or (saved.provider if saved else 'mock')).lower()
    model = src.get('model') or (saved.model if saved else 'deepseek/deepseek-chat-v3-0324:free')
    base_url = (src.get('base_url') or (saved.base_url if saved else 'https://openrouter.ai/api/v1')).rstrip('/')
    endpoint = base_url if base_url.endswith('/chat/completions') else f"{base_url}/chat/completions"

    incoming_key = src.get('api_key')
    api_key = saved.api_key if saved else None
    if incoming_key and not str(incoming_key).startswith('********'):
        api_key = incoming_key

    if provider == 'mock':
        s = LLMSettings(provider=provider, base_url=base_url, api_key=api_key, model=model, timeout_seconds=int(src.get('timeout_seconds') or (saved.timeout_seconds if saved else 120)), temperature=float(src.get('temperature') or (saved.temperature if saved else 0.2)), is_active=True, last_connection_status='mock', last_latency_ms=0, last_error=None, last_actual_model=model)
        db.add(s); db.commit()
        return {'ok': True, 'provider': 'mock', 'endpoint': 'mock://local', 'model': model, 'status':'mock', 'latency_ms':0}

    has_api_key = bool(api_key and not str(api_key).startswith('********'))
    key_tail = (api_key[-4:] if has_api_key else 'none')
    if provider != 'mock' and not has_api_key:
        raise HTTPException(400, {'ok': False, 'provider': provider, 'model': model, 'endpoint': endpoint, 'status': 'config', 'response_body': 'API key is empty', 'has_api_key': False, 'key_tail': key_tail})
    body = {'model': model, 'messages': [{'role': 'user', 'content': 'ping'}], 'max_tokens': int(src.get('max_tokens') or 20), 'temperature': float(src.get('temperature') or (saved.temperature if saved else 0.2))}
    req = request.Request(
        url=endpoint,
        data=json.dumps(body).encode(),
        method='POST',
        headers={
            'Authorization': f"Bearer {api_key or ''}",
            'Content-Type': 'application/json',
            'HTTP-Referer': 'http://localhost',
            'X-Title': 'AI Discovery Platform',
        }
    )
    try:
        started = time.time()
        with request.urlopen(req, timeout=int(src.get('timeout_seconds') or (saved.timeout_seconds if saved else 120))) as resp:
            data = json.loads(resp.read().decode())
            actual_model = data.get('model') or model
            latency_ms = int((time.time()-started)*1000)
            srow = LLMSettings(provider=provider, base_url=base_url, api_key=api_key, model=model, timeout_seconds=int(src.get('timeout_seconds') or (saved.timeout_seconds if saved else 120)), temperature=float(src.get('temperature') or (saved.temperature if saved else 0.2)), is_active=True, last_connection_status='connected', last_latency_ms=latency_ms, last_error=None, last_actual_model=actual_model)
            db.add(srow); db.commit()
            return {'ok': True, 'provider': provider, 'endpoint': endpoint, 'model': model, 'actual_model': actual_model, 'status':'connected', 'latency_ms':latency_ms, 'has_api_key': has_api_key, 'key_tail': key_tail, 'message': str(data)[:160]}
    except error.HTTPError as e:
        text = e.read().decode(errors='ignore')
        if provider == 'openrouter' and model != 'openrouter/free':
            return test_llm({**src, 'model': 'openrouter/free'}, db)
        srow = LLMSettings(provider=provider, base_url=base_url, api_key=api_key, model=model, timeout_seconds=int(src.get('timeout_seconds') or (saved.timeout_seconds if saved else 120)), temperature=float(src.get('temperature') or (saved.temperature if saved else 0.2)), is_active=True, last_connection_status='error', last_latency_ms=None, last_error=text[:500], last_actual_model=None)
        db.add(srow); db.commit()
        raise HTTPException(400, {'ok': False, 'provider': provider, 'model': model, 'endpoint': endpoint, 'status': 'error', 'response_body': text[:500], 'has_api_key': has_api_key, 'key_tail': key_tail})
    except Exception as e:
        srow = LLMSettings(provider=provider, base_url=base_url, api_key=api_key, model=model, timeout_seconds=int(src.get('timeout_seconds') or (saved.timeout_seconds if saved else 120)), temperature=float(src.get('temperature') or (saved.temperature if saved else 0.2)), is_active=True, last_connection_status='error', last_latency_ms=None, last_error=str(e)[:500], last_actual_model=None)
        db.add(srow); db.commit()
        raise HTTPException(400, {'ok': False, 'provider': provider, 'model': model, 'endpoint': endpoint, 'status': 'error', 'response_body': str(e), 'has_api_key': has_api_key, 'key_tail': key_tail})
