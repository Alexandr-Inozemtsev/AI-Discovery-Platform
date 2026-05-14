from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
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
from app.services.content_extraction import extract_text_from_upload
from fastapi.responses import StreamingResponse
import json
from urllib import request, error
import time
import re
import uuid

router = APIRouter(prefix="/api", tags=["discovery"])
orchestrator = None
critic = None
LLM_STATUS_SET = {'mock','not_configured','connected','error','timeout','unauthorized','model_not_found','backend_error'}
SUPPORTED_CONTEXT_EXTENSIONS = {'txt', 'md', 'csv', 'docx', 'pdf', 'xlsx', 'xls'}
MAX_CONTEXT_FILE_SIZE = 15 * 1024 * 1024

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

def _mask_key(key: str | None) -> tuple[str, str]:
    k = (key or '').strip()
    if not k:
        return '', ''
    tail = k[-4:] if len(k) >= 4 else k
    return f"********{tail}", tail

def _status_message(status: str) -> str:
    messages = {
        'mock': 'Mock режим активен. Генерация доступна без внешнего провайдера.',
        'not_configured': 'LLM не настроена. Заполните Provider, Base URL, Model и API Key.',
        'connected': 'Подключение к LLM успешно.',
        'error': 'Ошибка подключения к LLM. Проверьте настройки.',
        'timeout': 'Превышено время ожидания ответа от LLM.',
        'unauthorized': 'Ошибка авторизации. Проверьте API key.',
        'model_not_found': 'Модель недоступна или указана неверно.',
        'backend_error': 'Ошибка backend при проверке LLM.'
    }
    return messages.get(status, 'Состояние LLM неизвестно.')

def _normalize_llm_status(raw_status: str | None, last_error: str | None = None) -> str:
    rs = (raw_status or '').lower().strip()
    err = (last_error or '').lower()
    if rs in LLM_STATUS_SET:
        return rs
    if rs in {'ok', 'success'}:
        return 'connected'
    if rs in {'config', 'not_ready'}:
        return 'not_configured'
    if '401' in err or '403' in err or 'unauthorized' in err:
        return 'unauthorized'
    if 'timeout' in err or 'timed out' in err:
        return 'timeout'
    if 'model' in err and ('not found' in err or 'does not exist' in err):
        return 'model_not_found'
    return 'error' if rs else 'not_configured'

def _serialize_llm_settings_row(s: LLMSettings | None) -> dict:
    provider = ((s.provider if s else 'mock') or 'mock').lower()
    base_url = (s.base_url if s else 'https://openrouter.ai/api/v1') or ''
    model = (s.model if s else 'deepseek/deepseek-chat-v3-0324:free') or ''
    timeout_seconds = int((s.timeout_seconds if s else 120) or 120)
    temperature = float((s.temperature if s else 0.2) or 0.2)
    masked, tail = _mask_key(s.api_key if s else '')
    has_required = provider == 'mock' or (bool(base_url.strip()) and bool(model.strip()) and bool(tail))
    raw_status = (s.last_connection_status if s else None) or ('mock' if provider == 'mock' else 'not_configured')
    status = _normalize_llm_status(raw_status, s.last_error if s else None)
    if not has_required and provider != 'mock':
        status = 'not_configured'
    return {
        'ok': True,
        'provider': provider,
        'base_url': base_url,
        'model': model,
        'api_key': masked,
        'key_tail': tail,
        'timeout_seconds': timeout_seconds,
        'temperature': temperature,
        'last_connection_status': status,
        'last_latency_ms': (s.last_latency_ms if s else 0) or 0,
        'last_actual_model': (s.last_actual_model if s else '') or '',
        'last_error': (s.last_error if s else None),
        'human_message': _status_message(status)
    }

def _runtime_status(db: Session) -> dict:
    s = db.query(LLMSettings).order_by(LLMSettings.id.desc()).first()
    payload = _serialize_llm_settings_row(s)
    configured = payload['provider'] == 'mock' or (bool(payload['base_url']) and bool(payload['model']) and bool(payload['key_tail']))
    ready = payload['provider'] == 'mock' or (configured and payload['last_connection_status'] == 'connected')
    return {
        'backend': {'status': 'ok'},
        'llm': {
            'provider': payload['provider'],
            'configured': configured,
            'ready_for_generation': ready,
            'last_connection_status': payload['last_connection_status'],
            'model': payload['model'],
            'last_actual_model': payload['last_actual_model'],
            'last_error': payload['last_error'],
            'human_message': payload['human_message']
        }
    }

def _ensure_llm_ready(db: Session):
    status = _runtime_status(db)
    if status['llm']['ready_for_generation']:
        return
    raise HTTPException(400, {
        'ok': False,
        'error': 'LLM_NOT_READY',
        'human_message': 'LLM не настроена. Откройте Настройки → LLM настройки и проверьте подключение.',
        'details': status['llm']
    })

def _context_source_status(extraction_status: str) -> str:
    if extraction_status == 'completed':
        return 'ready'
    if extraction_status == 'empty':
        return 'empty'
    if extraction_status == 'unsupported':
        return 'unsupported'
    if extraction_status in {'failed', 'unsupported'}:
        return 'error'
    return 'uploaded'

def _file_ext(filename: str) -> str:
    return (filename or '').lower().rsplit('.', 1)[-1] if '.' in (filename or '') else ''

def _normalize_context_source(raw: dict, project_id: str, kind: str) -> dict:
    src = raw if isinstance(raw, dict) else ({'url': str(raw)} if kind == 'link' else {'fileName': str(raw), 'title': str(raw)})
    now = str(src.get('updatedAt') or src.get('updated_at') or src.get('createdAt') or src.get('created_at') or '')
    source_id = src.get('id') or f"{kind}_{uuid.uuid4().hex[:12]}"
    title = src.get('title') or src.get('name') or src.get('fileName') or src.get('filename') or src.get('url') or 'Без названия'
    status = src.get('status') or ('ready' if src.get('extracted_text') or src.get('text_content') or src.get('chunks') else 'uploaded')
    chunks = src.get('chunks') if isinstance(src.get('chunks'), list) else []
    normalized = {
        **src,
        'id': source_id,
        'projectId': src.get('projectId') or src.get('project_id') or project_id,
        'title': title,
        'type': src.get('type') or ('url' if kind == 'link' else _file_ext(str(title)) or 'file'),
        'fileName': src.get('fileName') or src.get('filename') or src.get('name'),
        'url': src.get('url'),
        'size': int(src.get('size') or 0),
        'createdAt': src.get('createdAt') or src.get('created_at') or now,
        'updatedAt': src.get('updatedAt') or src.get('updated_at') or now,
        'status': status,
        'errorMessage': src.get('errorMessage') or src.get('error_message') or src.get('text_extraction_error'),
        'chunksCount': int(src.get('chunksCount') or src.get('chunks_count') or len(chunks)),
    }
    if normalized.get('name') is None and normalized.get('fileName'):
        normalized['name'] = normalized['fileName']
    return normalized

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

@router.post('/projects/{project_id}/context/sources/upload')
async def upload_context_sources(project_id: str, files: list[UploadFile] = File(...), db: Session = Depends(get_db)):
    p = repo.get_project(db, project_id)
    if not p:
        raise HTTPException(404, 'Проект не найден')
    sources = []
    for upload in files:
        content = await upload.read()
        ext = _file_ext(upload.filename or '')
        now = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
        base = {
            'id': f"doc_{uuid.uuid4().hex[:12]}",
            'projectId': project_id,
            'title': upload.filename or 'Без названия',
            'type': ext or (upload.content_type or 'file'),
            'fileName': upload.filename or '',
            'name': upload.filename or '',
            'size': len(content),
            'createdAt': now,
            'updatedAt': now,
            'mimeType': upload.content_type,
            'status': 'uploaded',
            'errorMessage': None,
            'chunksCount': 0,
        }
        if len(content) > MAX_CONTEXT_FILE_SIZE:
            sources.append({
                **base,
                'status': 'error',
                'text_extraction_status': 'failed',
                'text_extraction_error': 'Файл слишком большой. Максимальный размер: 15 МБ.',
                'text_extracted_at': None,
                'extracted_text': '',
                'chunks': [],
                'chunksCount': 0,
                'errorMessage': 'Файл слишком большой. Максимальный размер: 15 МБ.'
            })
            continue
        if ext not in SUPPORTED_CONTEXT_EXTENSIONS:
            sources.append({
                **base,
                'status': 'unsupported',
                'text_extraction_status': 'unsupported',
                'text_extraction_error': f'Неподдерживаемый формат файла: {ext or "unknown"}',
                'text_extracted_at': None,
                'extracted_text': '',
                'chunks': [],
                'chunksCount': 0,
                'errorMessage': f'Неподдерживаемый формат файла: {ext or "unknown"}'
            })
            continue
        extracted = extract_text_from_upload(upload.filename or '', content, upload.content_type)
        chunks = [
            {**chunk, 'sourceId': base['id'], 'projectId': project_id, 'metadata': {'fileName': base['fileName'], 'type': base['type']}}
            for chunk in (extracted.get('chunks') or [])
        ]
        extraction_status = extracted.get('status') or 'failed'
        sources.append({
            **base,
            'status': _context_source_status(extraction_status),
            'text_extraction_status': extraction_status,
            'text_extraction_error': extracted.get('error'),
            'errorMessage': extracted.get('error'),
            'text_extracted_at': now if extraction_status == 'completed' else None,
            'extracted_text': extracted.get('text') or '',
            'chunks': chunks,
            'chunksCount': len(chunks),
        })
    existing = repo.get_artifact(db, project_id, ArtifactType.CONTEXT)
    previous = existing.structured_content if existing and isinstance(existing.structured_content, dict) else {}
    merged_files = [*(previous.get('uploaded_files') or previous.get('documents') or []), *sources]
    structured = {
        **previous,
        'context_input': previous.get('context_input') or {},
        'documents': merged_files,
        'uploaded_files': merged_files,
        'links': previous.get('links') or [],
        'indexing_status': 'requires_update',
        'uploaded_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
    }
    repo.upsert_artifact(db, project_id, ArtifactType.CONTEXT, existing.content if existing else '', structured_content=structured)
    return {'ok': True, 'sources': sources}


@router.post('/projects/{project_id}/context/analyze')
def analyze_context(project_id: str, payload: dict, db: Session = Depends(get_db)):
    _ensure_llm_ready(db)
    p = repo.get_project(db, project_id)
    if not p:
        raise HTTPException(404, 'Проект не найден')
    existing = repo.get_artifact(db, project_id, ArtifactType.CONTEXT)
    context_input = payload.get('context_input') or {}
    links = payload.get('links') or []
    documents = payload.get('documents') or []
    documents = [_normalize_context_source(d, project_id, 'document') for d in documents]
    links = [_normalize_context_source(l, project_id, 'link') for l in links]
    orchestrator = AgentOrchestrator(create_llm(db))
    agent = orchestrator.get_agent(ArtifactType.CONTEXT.value)
    if not agent or not hasattr(agent, 'analyze'):
        raise HTTPException(500, 'ContextIngestionAgent не подключен в AgentOrchestrator')
    prev_structured = existing.structured_content if existing and isinstance(existing.structured_content, dict) else {}
    previous_context = {
        'context_input': prev_structured.get('context_input') or {},
        'extracted_knowledge': prev_structured.get('extracted_knowledge') or {},
        'knowledge_history': prev_structured.get('knowledge_history') or [],
        'knowledge_coverage': prev_structured.get('knowledge_coverage') or {},
        'missing_information': (prev_structured.get('extracted_knowledge') or {}).get('missing_information') or []
    }
    try:
        analysis = agent.analyze(
            p,
            {'context_input': context_input, 'documents': documents, 'links': links},
            previous_context=previous_context
        )
    except ValueError as e:
        raise HTTPException(400, str(e))
    extracted = analysis.get('extracted_knowledge') or {}
    if not extracted:
        raise HTTPException(400, 'LLM вернул некорректный JSON')
    source_trace = analysis.get('source_trace') or extracted.get('source_trace') or []
    coverage = analysis.get('coverage') or extracted.get('coverage') or {}
    readiness = analysis.get('readiness') or extracted.get('readiness') or {}
    problem_handoff = analysis.get('problem_handoff') or extracted.get('problem_handoff') or {}
    history = (existing.structured_content or {}).get('knowledge_history', []) if existing else []
    indexed_at = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
    snapshot = {
        'created_at': indexed_at,
        'extracted_knowledge': extracted,
        'documents': documents,
        'links': links,
        'source_trace': source_trace,
        'coverage': coverage,
        'readiness': readiness,
        'problem_handoff': problem_handoff,
    }
    history.append(snapshot)
    structured = {
        'context_input': context_input,
        'documents': documents,
        'uploaded_files': documents,
        'links': links,
        'extracted_knowledge': extracted,
        'source_trace': source_trace,
        'coverage': coverage,
        'readiness': readiness,
        'overview_for_ai': analysis.get('overview_for_ai') or {},
        'problem_handoff': problem_handoff,
        'knowledge_history': history[-30:],
        'indexing_status': 'completed',
        'indexed_at': indexed_at,
    }
    content = existing.content if existing else ''
    repo.upsert_artifact(db, project_id, ArtifactType.CONTEXT, content, structured_content=structured)
    return {
        'ok': True,
        'extracted_knowledge': extracted,
        'source_trace': source_trace,
        'coverage': coverage,
        'readiness': readiness,
        'problem_handoff': problem_handoff,
        'history_count': len(history),
        'indexing_status': 'completed',
    }

@router.post('/projects/{project_id}/generate/{artifact_type}', response_model=ArtifactRead)
def generate_artifact(project_id: str, artifact_type: ArtifactType, db: Session = Depends(get_db)):
    _ensure_llm_ready(db)
    p = repo.get_project(db, project_id)
    if not p: raise HTTPException(404, 'Проект не найден')
    orchestrator = AgentOrchestrator(create_llm(db))
    agent = orchestrator.get_agent(artifact_type.value)
    if not agent: raise HTTPException(400, 'Генерация для этого типа артефакта не поддерживается')
    try:
        existing=_existing_artifacts_map(db, project_id)
        ctx={k: v['content'] for k, v in existing.items()}
        current = existing.get(artifact_type.value, {})
        sc = current.get('structured_content') or {}
        qa_items = sc.get('ai_questions') or []
        answered = [q for q in qa_items if isinstance(q, dict) and str(q.get('answer','')).strip()]
        if answered:
            ctx['AI_QA_CONTEXT'] = json.dumps(answered, ensure_ascii=False)
        content = agent.run(p, ctx)
    except Exception as e:
        if 'openrouter' in str(e).lower() or '401' in str(e) or 'timeout' in str(e).lower():
            raise HTTPException(400, 'OpenRouter недоступен. Проверьте API key, модель и интернет-соединение.')
        raise
    return repo.upsert_artifact(db, project_id, artifact_type, content, None)

@router.post('/projects/{project_id}/validate', response_model=ArtifactRead)
def validate_project(project_id: str, db: Session = Depends(get_db)):
    _ensure_llm_ready(db)
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

def _default_stage_ai_structured():
    return {'ai_questions':[], 'ai_answers':[], 'ai_patch':{}, 'ai_history':[]}

def _default_problem_structured():
    return {
        'main_problem':'','user_pains':[],'business_pains':[],'root_causes':[],'consequences_if_not_solved':[],'evidence_signals':[],
        'problem_statement':'','assumptions':[],'missing_information':[],'clarifying_questions':[],'ai_chat_history':[],
        'versions':[],'status':'draft','source_context_version':0,'source_context_indexed_at':None,
        'problem_handoff':{},'source_trace':[],'context_readiness':{}
    }


@router.post('/projects/{project_id}/problem/generate')
def generate_problem(project_id: str, payload: dict | None = None, db: Session = Depends(get_db)):
    _ensure_llm_ready(db)
    p = repo.get_project(db, project_id)
    if not p: raise HTTPException(404, 'Проект не найден')
    context_art = repo.get_artifact(db, project_id, ArtifactType.CONTEXT)
    if not context_art or not (context_art.structured_content or {}).get('context_input'):
        raise HTTPException(400, 'Сначала заполните Контекст или загрузите источники знаний.')
    context_struct = context_art.structured_content or {}
    problem_handoff = context_struct.get('problem_handoff') or {}
    source_trace = context_struct.get('source_trace') or []
    context_readiness = context_struct.get('readiness') or {}
    problem_art = repo.get_artifact(db, project_id, ArtifactType.PROBLEM)
    prev = (problem_art.structured_content or _default_problem_structured()) if problem_art else _default_problem_structured()
    answered_questions = [
        q for q in (prev.get('ai_questions') or prev.get('clarifying_questions') or [])
        if isinstance(q, dict) and str(q.get('answer', '')).strip()
    ]
    prompt=(
        "Ты AI-ассистент бизнес-аналитика в Discovery-процессе. Отвечай строго на русском языке. "
        "На этапе 'Проблема' помоги сформулировать только проблему, без TO BE/решений/требований. Учитывай: 1) ручной текст PO в main_problem, 2) только отвеченные ai_questions, 3) контекст. Верни только JSON: "
        "{'main_problem':'','user_pains':[{'role':'','pain':'','example':'','source':''}],'business_pains':[{'type':'','description':'','impact':''}],"
        "'root_causes':[{'cause':'','category':'process|system|data|people|regulation|integration|unknown','confidence':'high|medium|low'}],"
        "'consequences_if_not_solved':[],'evidence_signals':[],'clarifying_questions':[],'problem_statement':'','assumptions':[],'missing_information':[]}. "
        f"Context problem_handoff: {json.dumps(problem_handoff, ensure_ascii=False)}. "
        f"Context source_trace: {json.dumps(source_trace, ensure_ascii=False)}. "
        f"Context readiness: {json.dumps(context_readiness, ensure_ascii=False)}. "
        f"Контекст: {json.dumps(context_struct, ensure_ascii=False)}. Текущий драфт проблемы: {json.dumps(prev, ensure_ascii=False)}. Ответы на вопросы: {json.dumps(answered_questions, ensure_ascii=False)}"
    )
    data = _json_from_llm_response(create_llm(db).generate(prompt))
    if not data:
        main_problem = (prev.get('main_problem') or '').strip()
        context_input = context_struct.get('context_input') or {}
        initiative = str(p.project_name or '').strip()
        summary = str(context_input.get('short_description') or '').strip()
        answered_lines = [
            f"{i+1}) {q.get('text', '').strip()} — {q.get('answer', '').strip()}"
            for i, q in enumerate(answered_questions)
            if str(q.get('text', '')).strip() and str(q.get('answer', '')).strip()
        ]
        problem_lines = []
        if main_problem:
            problem_lines.append(f"1) {main_problem}")
        if initiative or summary:
            problem_lines.append(f"{len(problem_lines)+1}) Контекст инициативы «{initiative or 'без названия'}»: {summary or 'описание уточняется'}.")
        if answered_lines:
            problem_lines.append(f"{len(problem_lines)+1}) Уточнения от пользователя: " + " | ".join(answered_lines))
        data = {
            'main_problem': main_problem or f"Не автоматизирован процесс по инициативе «{initiative or 'без названия'}».",
            'problem_statement': "\n".join(problem_lines).strip(),
            'clarifying_questions': prev.get('clarifying_questions') or [],
            'missing_information': [] if answered_lines else ['Требуются ответы на уточняющие вопросы'],
            'assumptions': prev.get('assumptions') or []
        }
    versions = prev.get('versions', [])
    versions.append({'created_at': str(time.time()), 'snapshot': {k:v for k,v in prev.items() if k!='versions'}})
    merged = {
        **_default_problem_structured(),
        **prev,
        **data,
        'versions': versions[-20:],
        'status':'needs_clarification',
        'source_context_version': context_art.version,
        'source_context_indexed_at': context_struct.get('indexed_at'),
        'problem_handoff': problem_handoff,
        'source_trace': source_trace,
        'context_readiness': context_readiness,
    }
    gen_list = data.get('generated_problem_list') or []
    if isinstance(gen_list, list) and gen_list:
        merged['generated_problem_list'] = gen_list
        merged['problem_statement'] = '\n'.join([f"{i+1}) {x}" for i,x in enumerate(gen_list)])
    if not (merged.get('problem_statement') or '').strip():
        strict_items: list[str] = []
        main_problem = str(merged.get('main_problem') or '').strip()
        if main_problem:
            strict_items.append(main_problem)
        for p_item in (merged.get('user_pains') or []):
            if isinstance(p_item, dict) and str(p_item.get('pain') or '').strip():
                strict_items.append(str(p_item.get('pain')).strip())
        for p_item in (merged.get('business_pains') or []):
            if isinstance(p_item, dict) and str(p_item.get('description') or '').strip():
                strict_items.append(str(p_item.get('description')).strip())
        for q in answered_questions:
            txt = str(q.get('answer') or '').strip()
            if txt:
                strict_items.append(f"Подтверждено пользователем: {txt}")
        dedup: list[str] = []
        seen: set[str] = set()
        for item in strict_items:
            key = item.lower()
            if key not in seen:
                seen.add(key)
                dedup.append(item)
        merged['problem_statement'] = '\n'.join([f"{i+1}) {x}" for i, x in enumerate(dedup[:8])]) if dedup else ''
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
    _ensure_llm_ready(db)
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



@router.post('/projects/{project_id}/stage/{artifact_type}/questions')
def stage_questions(project_id: str, artifact_type: ArtifactType, db: Session = Depends(get_db)):
    _ensure_llm_ready(db)
    context_art = repo.get_artifact(db, project_id, ArtifactType.CONTEXT)
    if not context_art:
        raise HTTPException(400, 'Сначала заполните Контекст')
    art = repo.get_artifact(db, project_id, artifact_type)
    sc = (art.structured_content if art else {}) or {}
    prompt = f"Сформируй 3-5 дополнительных уточняющих вопросов на русском для этапа {artifact_type.value} на основе контекста. Верни JSON: {{questions:[]}}. Контекст: {json.dumps(context_art.structured_content or context_art.content, ensure_ascii=False)}"
    raw = create_llm(db).generate(prompt)
    data = _json_from_llm_response(raw)
    new_questions = data.get('questions') if isinstance(data, dict) else []
    if not isinstance(new_questions, list): new_questions = []
    existing = sc.get('ai_questions') or []
    existing_texts = {str(q.get('text','')).strip().lower() for q in existing if isinstance(q, dict)}
    for q in new_questions:
        txt = str(q).strip()
        if txt and txt.lower() not in existing_texts:
            existing.append({'id': f"q_{int(time.time()*1000)}_{len(existing)}", 'text': txt, 'answer': ''})
            existing_texts.add(txt.lower())
        if len(existing) >= 6:
            break
    existing = existing[:6]
    sc['ai_questions'] = existing
    saved = repo.upsert_artifact(db, project_id, artifact_type, (art.content if art else ''), structured_content=sc, rich_content_json=(art.rich_content_json if art else None), rendered_html=(art.rendered_html if art else None))
    return {'ok': True, 'questions': existing, 'structured_content': saved.structured_content}

@router.post('/projects/{project_id}/stage/{artifact_type}/ask')
def stage_ask(project_id: str, artifact_type: ArtifactType, payload: dict, db: Session = Depends(get_db)):
    _ensure_llm_ready(db)
    art = repo.get_artifact(db, project_id, artifact_type)
    sc = (art.structured_content if art else {}) or {}
    msg = payload.get('message','').strip()
    qid = payload.get('question_id')
    if not msg:
        raise HTTPException(400, 'Введите ответ для AI')
    questions = sc.get('ai_questions') or []
    q_text = ''
    for q in questions:
        if isinstance(q, dict) and q.get('id') == qid:
            q['answer'] = msg
            q_text = q.get('text','')
    sc['ai_questions'] = questions
    prompt = f"На этапе {artifact_type.value} предложи патч к артефакту на русском. Вопрос: {q_text}. Ответ пользователя: {msg}. Верни JSON-объект patch."
    llm = create_llm(db)
    raw = llm.generate(prompt)
    patch = _json_from_llm_response(raw) or {'note': msg}
    sc.setdefault('ai_answers', []).append({'question_id': qid, 'question': q_text, 'answer': msg, 'answered_at': str(time.time())})
    sc['ai_patch'] = patch
    sc.setdefault('ai_history', []).append({'q': msg, 'raw': raw})
    saved = repo.upsert_artifact(db, project_id, artifact_type, (art.content if art else ''), structured_content=sc, rich_content_json=(art.rich_content_json if art else None), rendered_html=(art.rendered_html if art else None))
    return {'ok': True, 'patch': patch, 'structured_content': saved.structured_content}

@router.post('/projects/{project_id}/stage/{artifact_type}/apply-patch')
def stage_apply_patch(project_id: str, artifact_type: ArtifactType, payload: dict, db: Session = Depends(get_db)):
    art = repo.get_artifact(db, project_id, artifact_type)
    if not art: raise HTTPException(404, 'Артефакт не найден')
    sc = (art.structured_content or {})
    patch = payload.get('patch') or sc.get('ai_patch') or {}
    if isinstance(patch, dict):
        sc.update(patch)
    saved = repo.upsert_artifact(db, project_id, artifact_type, art.content, structured_content=sc, rich_content_json=art.rich_content_json, rendered_html=art.rendered_html)
    return {'ok': True, 'structured_content': saved.structured_content}

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
    return _serialize_llm_settings_row(s)

@router.put('/settings/llm')
def put_llm_settings(payload: dict, db: Session = Depends(get_db)):
    old = db.query(LLMSettings).order_by(LLMSettings.id.desc()).first()
    incoming = payload.get('api_key')
    api_key = old.api_key if old else None
    if incoming and not str(incoming).startswith('********') and not str(incoming).strip()=='':
        api_key = incoming
    s = LLMSettings(provider=payload.get('provider','mock'), base_url=payload.get('base_url'), api_key=api_key, model=payload.get('model'), timeout_seconds=payload.get('timeout_seconds',60), temperature=payload.get('temperature',0.2), is_active=True, last_connection_status=(old.last_connection_status if old else None), last_latency_ms=(old.last_latency_ms if old else None), last_error=(old.last_error if old else None), last_actual_model=(old.last_actual_model if old else None))
    db.add(s); db.commit(); db.refresh(s)
    return _serialize_llm_settings_row(s)

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
        db.add(s); db.commit(); db.refresh(s)
        return _serialize_llm_settings_row(s)

    has_api_key = bool(api_key and not str(api_key).startswith('********'))
    key_tail = (api_key[-4:] if has_api_key else 'none')
    if provider != 'mock' and not has_api_key:
        srow = LLMSettings(provider=provider, base_url=base_url, api_key=api_key, model=model, timeout_seconds=int(src.get('timeout_seconds') or (saved.timeout_seconds if saved else 120)), temperature=float(src.get('temperature') or (saved.temperature if saved else 0.2)), is_active=True, last_connection_status='not_configured', last_latency_ms=0, last_error='API key отсутствует', last_actual_model=None)
        db.add(srow); db.commit(); db.refresh(srow)
        return _serialize_llm_settings_row(srow)
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
            db.add(srow); db.commit(); db.refresh(srow)
            return _serialize_llm_settings_row(srow)
    except error.HTTPError as e:
        text = e.read().decode(errors='ignore')
        status = 'unauthorized' if e.code in (401,403) else ('model_not_found' if 'model' in text.lower() and ('not found' in text.lower() or 'does not exist' in text.lower()) else 'backend_error')
        srow = LLMSettings(provider=provider, base_url=base_url, api_key=api_key, model=model, timeout_seconds=int(src.get('timeout_seconds') or (saved.timeout_seconds if saved else 120)), temperature=float(src.get('temperature') or (saved.temperature if saved else 0.2)), is_active=True, last_connection_status=status, last_latency_ms=None, last_error=text[:500], last_actual_model=None)
        db.add(srow); db.commit(); db.refresh(srow)
        return _serialize_llm_settings_row(srow)
    except Exception as e:
        txt = str(e)
        status = 'timeout' if ('timed out' in txt.lower() or 'timeout' in txt.lower()) else 'backend_error'
        srow = LLMSettings(provider=provider, base_url=base_url, api_key=api_key, model=model, timeout_seconds=int(src.get('timeout_seconds') or (saved.timeout_seconds if saved else 120)), temperature=float(src.get('temperature') or (saved.temperature if saved else 0.2)), is_active=True, last_connection_status=status, last_latency_ms=None, last_error=txt[:500], last_actual_model=None)
        db.add(srow); db.commit(); db.refresh(srow)
        return _serialize_llm_settings_row(srow)

@router.get('/runtime/status')
def runtime_status(db: Session = Depends(get_db)):
    return _runtime_status(db)
