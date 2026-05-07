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


def _llm_error(stage:str, provider:str, model:str, error:str, details:str=''):
    return {'ok':False,'error':error,'details':details,'stage':stage,'provider':provider,'model':model}

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
    links = payload.get('links') or []
    documents = payload.get('documents') or []
    existing = repo.get_artifact(db, project_id, ArtifactType.CONTEXT)
    prompt = (
        'Верни только JSON и строго на русском языке. '
        'Это этап ingestion, без рисков/рекомендаций/гипотез/TO-BE. '
        'Структура JSON: '
        '{"процессы":[],"системы":[],"роли":[],"интеграции":[],"kpi":[],"бизнес_сущности":[],"документы":[],"термины":[],"покрытие":{"документы":false,"системы":false,"процессы":false,"bpmn":false,"kpi":false,"sla":false}}. '
        f'Проект: {p.project_name}. Overview: {json.dumps(context_input, ensure_ascii=False)}. '
        f'Ссылки: {json.dumps(links, ensure_ascii=False)}. Документы: {json.dumps(documents, ensure_ascii=False)}'
    )
    llm = create_llm(db)
    raw = llm.generate(prompt)
    extracted = _json_from_llm_response(raw)
    if not extracted:
        raise HTTPException(400, 'LLM вернул некорректный JSON')
    history = (existing.structured_content or {}).get('knowledge_history', []) if existing else []
    snapshot = {'created_at': str(time.time()), 'extracted_knowledge': extracted, 'documents': documents, 'links': links}
    history.append(snapshot)
    structured = {
        'context_input': context_input,
        'documents': documents,
        'links': links,
        'extracted_knowledge': extracted,
        'knowledge_history': history[-30:],
        'indexing_status': 'completed'
    }
    content = existing.content if existing else ''
    repo.upsert_artifact(db, project_id, ArtifactType.CONTEXT, content, structured_content=structured)
    return {'ok': True, 'extracted_knowledge': extracted, 'history_count': len(history), 'indexing_status': 'completed'}

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





def _default_goal_structured():
    now = str(time.time())
    return {
        'id':'','title':'','businessProblem':'','desiredOutcome':'','businessImportance':'','noActionImpact':'',
        'businessValue':{'fteSaving':None,'revenueImpact':None,'riskReduction':'','operationalEffect':''},
        'successMetrics':[],'nonGoals':[],'assumptions':[],'risks':[],'constraints':[],'stakeholders':[],
        'priority':'MEDIUM','status':'DRAFT','aiSummary':'','aiRecommendations':[],'aiQuestions':[],'aiContradictions':[],'aiDetectedProblems':[],
        'smartAnalysis':{'specific':{'status':'warning','comment':'Не заполнено','recommendation':'Уточните цель'},'measurable':{'status':'warning','comment':'Не заполнено','recommendation':'Добавьте KPI'},'achievable':{'status':'warning','comment':'Не заполнено','recommendation':'Опишите ограничения'},'relevant':{'status':'warning','comment':'Не заполнено','recommendation':'Покажите бизнес-ценность'},'timeBound':{'status':'error','comment':'Нет срока','recommendation':'Укажите срок'}},
        'completeness':0,'linkedProblems':[],'linkedRequirements':[],'linkedUseCases':[],'affectedSections':[],
        'history':[],'aiHistory':[],'createdAt':now,'updatedAt':now
    }


def _goal_to_text(sc:dict):
    metrics = '; '.join([f"{m.get('metric','')}: {m.get('currentValue','—')} -> {m.get('targetValue','')}" for m in (sc.get('successMetrics') or [])])
    return f"Цель инициативы: {sc.get('title','')}\nПроблема: {sc.get('businessProblem','')}\nРезультат: {sc.get('desiredOutcome','')}\nKPI: {metrics}"

def _default_problem_structured():
    return {
        'main_problem':'','user_pains':[],'business_pains':[],'root_causes':[],'consequences_if_not_solved':[],'evidence_signals':[],
        'problem_statement':'','assumptions':[],'missing_information':[],'clarifying_questions':[],'ai_chat_history':[],
        'versions':[],'status':'draft','source_context_version':0
    }


@router.post('/projects/{project_id}/problem/generate')
def generate_problem(project_id: str, payload: dict | None = None, db: Session = Depends(get_db)):
    p = repo.get_project(db, project_id)
    if not p: raise HTTPException(404, 'Проект не найден')
    context_art = repo.get_artifact(db, project_id, ArtifactType.CONTEXT)
    if not context_art or not (context_art.structured_content or {}).get('context_input'):
        raise HTTPException(400, 'Сначала заполните Контекст или загрузите источники знаний.')
    problem_art = repo.get_artifact(db, project_id, ArtifactType.PROBLEM)
    prev = (problem_art.structured_content or _default_problem_structured()) if problem_art else _default_problem_structured()
    prompt=(
        "Ты AI-ассистент бизнес-аналитика в Discovery-процессе. Отвечай строго на русском языке. "
        "На этапе 'Проблема' помоги сформулировать только проблему, без TO BE/решений/требований. Верни только JSON: "
        "{'main_problem':'','user_pains':[{'role':'','pain':'','example':'','source':''}],'business_pains':[{'type':'','description':'','impact':''}],"
        "'root_causes':[{'cause':'','category':'process|system|data|people|regulation|integration|unknown','confidence':'high|medium|low'}],"
        "'consequences_if_not_solved':[],'evidence_signals':[],'clarifying_questions':[],'problem_statement':'','assumptions':[],'missing_information':[]}. "
        f"Контекст: {json.dumps(context_art.structured_content, ensure_ascii=False)}. Текущий драфт проблемы: {json.dumps(prev, ensure_ascii=False)}"
    )
    data = _json_from_llm_response(create_llm(db).generate(prompt))
    if not data: raise HTTPException(400, 'LLM вернул некорректный JSON')
    versions = prev.get('versions', [])
    versions.append({'created_at': str(time.time()), 'snapshot': {k:v for k,v in prev.items() if k!='versions'}})
    merged = {**_default_problem_structured(), **prev, **data, 'versions': versions[-20:], 'status':'needs_clarification', 'source_context_version': context_art.version}
    art = repo.upsert_artifact(db, project_id, ArtifactType.PROBLEM, merged.get('problem_statement') or merged.get('main_problem') or '', structured_content=merged)
    return {'ok':True,'structured_content':art.structured_content,'version':art.version}


@router.post('/projects/{project_id}/problem/ask')
def ask_problem(project_id: str, payload: dict, db: Session = Depends(get_db)):
    question = payload.get('message','')
    patch = {'clarifying_questions':[f"Уточнение: {question}"], 'missing_information':['Требуется подтверждение от пользователя']}
    return {'ok': True, 'patch': patch, 'assistant_message': 'Предлагаю добавить уточнения в черновик проблемы.'}


@router.post('/projects/{project_id}/problem/apply-patch')
def apply_problem_patch(project_id: str, payload: dict, db: Session = Depends(get_db)):
    art = repo.get_artifact(db, project_id, ArtifactType.PROBLEM)
    if not art: raise HTTPException(404, 'Артефакт проблемы не найден')
    sc = art.structured_content or _default_problem_structured()
    patch = payload.get('patch') or {}
    for k,v in patch.items():
        sc[k] = v
    sc['status'] = payload.get('status') or sc.get('status') or 'draft'
    saved = repo.upsert_artifact(db, project_id, ArtifactType.PROBLEM, sc.get('problem_statement') or sc.get('main_problem') or '', structured_content=sc)
    return {'ok':True, 'structured_content': saved.structured_content, 'version': saved.version}


@router.post('/projects/{project_id}/goal/generate')
def generate_goal(project_id: str, db: Session = Depends(get_db)):
    p = repo.get_project(db, project_id)
    if not p: raise HTTPException(404, 'Проект не найден')
    context_art = repo.get_artifact(db, project_id, ArtifactType.CONTEXT)
    if not context_art or not (context_art.content or (context_art.structured_content or {}).get('context_input')):
        raise HTTPException(400, 'Сначала заполните Контекст')
    problem_art = repo.get_artifact(db, project_id, ArtifactType.PROBLEM)
    goal_art = repo.get_artifact(db, project_id, ArtifactType.GOAL)
    prev = (goal_art.structured_content or _default_goal_structured()) if goal_art else _default_goal_structured()
    warning = None
    if not problem_art or not (problem_art.content or '').strip():
        warning = 'Проблема не заполнена. Цели будут сформированы только по Контексту.'
    prompt = (
        "Ты AI-ассистент бизнес-аналитика. Верни строго JSON на русском языке без markdown. "
        "Формат: {goal_options:[{title,description,focus,why_relevant,linked_problems,suggested_kpis,non_goals,assumptions}],"
        "recommended_goal:{title,business_problem,desired_outcome,success_metrics,non_goals,assumptions,risks},"
        "smart_analysis:{specific:{status,comment},measurable:{status,comment},achievable:{status,comment},relevant:{status,comment},time_bound:{status,comment}},"
        "questions:[],contradictions:[],missing_information:[]}. "
        f"Проект: {p.project_name}. CONTEXT: {json.dumps(context_art.structured_content or context_art.content, ensure_ascii=False)}. "
        f"PROBLEM: {json.dumps((problem_art.structured_content if problem_art else {}), ensure_ascii=False)}. "
        f"Текущий GOAL: {json.dumps(prev, ensure_ascii=False)}"
    )
    llm = create_llm(db)
    raw = ''
    try:
        raw = llm.generate(prompt)
    except Exception as e:
        raise HTTPException(400, _llm_error('GOAL', getattr(llm,'provider','unknown'), getattr(llm,'model','unknown'), 'Ошибка вызова LLM', str(e)))
    data = _json_from_llm_response(raw)
    if not data:
        prev_hist = merged.get('aiHistory') if 'merged' in locals() else []
        merged = {**_default_goal_structured(), **prev}
        merged['aiHistory'] = [*(prev_hist or []), {'createdAt': str(time.time()), 'raw_response': raw}][-30:]
        repo.upsert_artifact(db, project_id, ArtifactType.GOAL, _goal_to_text(merged), structured_content=merged)
        raise HTTPException(400, _llm_error('GOAL', getattr(llm,'provider','unknown'), getattr(llm,'model','unknown'), 'AI вернул неструктурированный ответ', raw[:1200]))
    merged = {**_default_goal_structured(), **prev}
    merged['aiQuestions'] = data.get('questions') or []
    merged['aiContradictions'] = data.get('contradictions') or []
    merged['aiRecommendations'] = data.get('missing_information') or []
    merged['status'] = 'AI_GENERATED'
    merged['updatedAt'] = str(time.time())
    merged['aiDrafts'] = data
    merged['aiHistory'] = [*((merged.get('aiHistory') or [])), {'createdAt': str(time.time()), 'response': data}][-30:]
    art = repo.upsert_artifact(db, project_id, ArtifactType.GOAL, _goal_to_text(merged), structured_content=merged)
    return {'ok':True,'warning':warning,'structured_content':art.structured_content,'draft':data,'version':art.version}

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
