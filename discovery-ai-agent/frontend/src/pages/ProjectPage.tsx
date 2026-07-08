import { Download, MoreHorizontal, Database, RefreshCcw, FileText, FileSpreadsheet, File, Link2, Figma, CheckCircle2, AlertTriangle, XCircle, Send } from 'lucide-react'
import RichEditor from '../components/RichEditor'
import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams, useSearchParams } from 'react-router-dom'
import { ApiError, api, apiForm, assistantApi } from '../api/client'
import { ArtifactType, AssistantAction, AssistantMessage, Project } from '../types/discovery'
import AIActionBar from '../ui/components/AIActionBar'
import AIAssistantPanel, { SuggestedActionKey } from '../ui/components/AIAssistantPanel'
import ErrorBoundary from '../components/ErrorBoundary'
import Button from '../ui/components/Button'
import ButtonLink from '../ui/components/ButtonLink'
import ContextStage from './project/context/ContextStage'





type GoalMetric = { metric:string; currentValue?:string; targetValue:string; measurement?:string; dataSource?:string }
type SmartKey = 'specific'|'measurable'|'achievable'|'relevant'|'timeBound'
type SmartState = { status:'ok'|'warning'|'error'; comment:string; recommendation:string }
type GoalDraft = {
  id:string; title:string; businessProblem:string; desiredOutcome:string; businessImportance:string; noActionImpact:string;
  businessValue:{fteSaving?:number; revenueImpact?:number; riskReduction?:string; operationalEffect?:string};
  successMetrics:GoalMetric[]; nonGoals:string[]; assumptions:string[]; risks:string[]; constraints:string[]; stakeholders:string[];
  priority:'LOW'|'MEDIUM'|'HIGH'|'CRITICAL'; status:'DRAFT'|'AI_GENERATED'|'VALIDATED'|'APPROVED';
  aiSummary?:string; aiRecommendations?:string[]; aiQuestions?:string[]; aiContradictions?:string[]; aiDetectedProblems?:string[];
  smartAnalysis?:Record<SmartKey,SmartState>; completeness?:number; linkedProblems?:string[]; linkedRequirements?:string[]; linkedUseCases?:string[];
  affectedSections?:string[]; history?:Array<{changedAt:string; changedBy:string; action:string}>; createdAt:string; updatedAt:string
}

const emptyGoal = ():GoalDraft => ({
  id: crypto.randomUUID(), title:'', businessProblem:'', desiredOutcome:'', businessImportance:'', noActionImpact:'', businessValue:{},
  successMetrics:[], nonGoals:[], assumptions:[], risks:[], constraints:[], stakeholders:[], priority:'MEDIUM', status:'DRAFT',
  aiRecommendations:[], aiQuestions:[], aiContradictions:[], aiDetectedProblems:[], linkedProblems:[], linkedRequirements:[], linkedUseCases:[], affectedSections:[], history:[],
  smartAnalysis:{specific:{status:'warning',comment:'Недостаточно данных',recommendation:'Уточните формулировку'}, measurable:{status:'warning',comment:'Нет KPI',recommendation:'Добавьте метрики'}, achievable:{status:'warning',comment:'Не описаны ограничения',recommendation:'Укажите ограничения'}, relevant:{status:'warning',comment:'Не отражена бизнес-ценность',recommendation:'Добавьте бизнес-эффект'}, timeBound:{status:'error',comment:'Не указан срок',recommendation:'Добавьте целевую дату'}},
  completeness:0, createdAt:new Date().toISOString(), updatedAt:new Date().toISOString()
})

type ContextInput = {
  initiative_name:string; short_description:string; initiative_goal:string; business_domain:string; process_owner:string; discovery_owner:string; related_processes:string; related_systems:string;
  product_goal?:string; business_process_owner?:string; discovery_responsible?:string;
}
const emptyInput:ContextInput={initiative_name:'',short_description:'',initiative_goal:'',business_domain:'',process_owner:'',discovery_owner:'',related_processes:'',related_systems:'',product_goal:'',business_process_owner:'',discovery_responsible:''}


const safeText=(value:any):string=>{
  if(value==null) return ''
  if(['string','number','boolean'].includes(typeof value)) return String(value)
  if(Array.isArray(value)) return value.map(safeText).filter(Boolean).join(', ')
  if(typeof value==='object') return String(value.name || value.title || value.label || JSON.stringify(value))
  return String(value)
}
const formatFileSize=(size:any)=>{
  const n = Number(size||0)
  if(!Number.isFinite(n) || n<=0) return '0 B'
  if(n<1024) return `${n} B`
  if(n<1024*1024) return `${(n/1024).toFixed(1)} KB`
  return `${(n/(1024*1024)).toFixed(2)} MB`
}

const tabs:{label:string;type:ArtifactType;desc:string}[]=[
{label:'Контекст',type:'CONTEXT',desc:'Бизнес-контекст, цели и ограничения.'},{label:'Проблема',type:'PROBLEM',desc:'Проблема и её последствия.'},{label:'Цель',type:'GOAL',desc:'Целевая формулировка и критерии успеха.'},
{label:'Бизнес-эффект',type:'BUSINESS_EFFECT',desc:'Качественные и количественные эффекты.'},{label:'AS IS',type:'AS_IS',desc:'Текущее состояние.'},{label:'TO BE',type:'TO_BE',desc:'Целевое состояние.'},
{label:'Use Cases',type:'USE_CASES',desc:'Ключевые сценарии пользователей.'},{label:'Требования',type:'FUNCTIONAL_REQUIREMENTS',desc:'Функциональные требования.'},{label:'Риски',type:'RISKS',desc:'Риски и меры.'},{label:'Финальный БТ',type:'FINAL_BT',desc:'Финальная бизнес-требование спецификация.'}]



const stageOrder:ArtifactType[]=['CONTEXT','PROBLEM','GOAL','BUSINESS_EFFECT','AS_IS','TO_BE','USE_CASES','FUNCTIONAL_REQUIREMENTS','RISKS','FINAL_BT']
const humanStage:Record<string,string>={CONTEXT:'Контекст',PROBLEM:'Проблема',GOAL:'Цель',BUSINESS_EFFECT:'Бизнес-эффект',AS_IS:'AS IS',TO_BE:'TO BE',USE_CASES:'Use Cases',FUNCTIONAL_REQUIREMENTS:'Требования',RISKS:'Риски',FINAL_BT:'Финальный БТ'}
const coverageRows=[['Документы','success'],['Процессы','success'],['Системы','success'],['Роли','success'],['Интеграции','success'],['KPI','warning'],['BPMN','error'],['SLA','error'],['Ограничения','warning']] as const

const workflowStages = [
  ['CONTEXT','Вы загружаете материалы и ссылки, описываете инициативу. AI индексирует и извлекает знания.'],
  ['PROBLEM','AI анализирует контекст и помогает сформулировать проблему, боли и корневые причины.'],
  ['GOAL','Определяем SMART-цель, метрики успеха и критерии результата.'],
  ['BUSINESS_EFFECT','AI помогает посчитать ожидаемый эффект: FTE, риски, скорость, доход, качество.'],
  ['AS_IS','AI строит текущий процесс на основе документов и извлечённых знаний.'],
  ['TO_BE','AI предлагает целевой процесс и варианты автоматизации.'],
  ['USE_CASES','AI формирует сценарии, negative flows и edge cases.'],
  ['FUNCTIONAL_REQUIREMENTS','AI помогает оформить функциональные и нефункциональные требования.'],
  ['RISKS','AI выявляет риски, зависимости, ограничения и rollback.'],
  ['FINAL_BT','AI собирает всё в единый бизнес-документ.']
] as const

const detectLinkType=(url:string)=>{const u=url.toLowerCase(); if(u.includes('jira')) return 'Jira'; if(u.includes('confluence')) return 'Confluence'; if(u.includes('figma')) return 'Figma'; if(u.includes('draw.io')) return 'Draw.io'; if(u.includes('swagger')) return 'Swagger'; if(u.includes('superset')) return 'Superset'; if(u.includes('kibana')) return 'Kibana'; if(u.includes('bi')) return 'BI'; return 'Другое'}

const sourceIcon=(name:string)=>{const n=name.toLowerCase(); if(n.includes('.pdf')) return 'pdf'; if(n.includes('.doc')) return 'doc'; if(n.includes('.xls')) return 'xls'; if(n.includes('jira')) return 'jira'; if(n.includes('confluence')) return 'confluence'; if(n.includes('figma')) return 'figma'; if(n.includes('bi')) return 'bi'; return 'default'}
const CONTEXT_FILE_EXTENSIONS = ['docx','pdf','txt','md','xlsx','xls','csv']
const MAX_CONTEXT_FILE_SIZE = 15 * 1024 * 1024
const extensionOf=(name:string)=>String(name||'').toLowerCase().split('.').pop()||''
const normalizeContextSource=(raw:any,projectId?:string,kind:'document'|'link'='document')=>{
  const now=new Date().toISOString()
  const title=raw?.title||raw?.name||raw?.fileName||raw?.url||'Без названия'
  const chunks=Array.isArray(raw?.chunks)?raw.chunks:[]
  return {
    ...raw,
    id: raw?.id || `${kind==='document'?'doc':'link'}_${Date.now()}_${Math.random().toString(16).slice(2,8)}`,
    projectId: raw?.projectId || projectId || '',
    title,
    name: raw?.name || raw?.fileName || title,
    fileName: raw?.fileName || raw?.name,
    type: raw?.type || (kind==='link'?'url':extensionOf(title)||'file'),
    size: Number(raw?.size||0),
    createdAt: raw?.createdAt || raw?.created_at || now,
    updatedAt: now,
    status: raw?.status || 'uploaded',
    errorMessage: raw?.errorMessage || raw?.text_extraction_error || '',
    chunksCount: Number(raw?.chunksCount || chunks.length || 0),
  }
}

const demoDocs=[
  {name:'BRD_Автопролонгация_ИБС_v1.0.pdf',size:'12.4 MB',date:'06.05.2026'},
  {name:'Описание процесса пролонгации ИБС.docx',size:'2.1 MB',date:'06.05.2026'},
  {name:'Отчет по обращениям клиентов.xlsx',size:'1.3 MB',date:'06.05.2026'}
]
const demoLinks=[
  {url:'Jira: SFA-12345 Автопролонгация ИБС',type:'Jira'},
  {url:'Confluence: Процесс пролонгации ИБС',type:'Confluence'},
  {url:'Figma: Прототип экрана',type:'Figma'},
  {url:'BI Dashboard: Просрочки ИБС',type:'Superset'}
]

export default function ProjectPage(){
  const {projectId}=useParams(); const navigate = useNavigate(); const [searchParams] = useSearchParams(); const [project,setProject]=useState<Project|null>(null); const [active,setActive]=useState<ArtifactType>('CONTEXT')
  const [content,setContent]=useState(''); const [richJson,setRichJson]=useState<any>(null); const [structured,setStructured]=useState<any>({}); const [ver,setVer]=useState<number|null>(null); const [updated,setUpdated]=useState('');
  const [cmp,setCmp]=useState<any>(null); const [pipeline,setPipeline]=useState<Record<string,any>>({}); const [msg,setMsg]=useState(''); const [aiActionLoading,setAiActionLoading]=useState<string|null>(null); const [aiActionStatus,setAiActionStatus]=useState<Record<string,'idle'|'success'|'error'>>({}); const [goalDraft,setGoalDraft]=useState<any>(null); const [busy,setBusy]=useState(false); const [saving,setSaving]=useState<'idle'|'saving'|'saved'|'error'>('idle');
  const [assistantSessionId,setAssistantSessionId]=useState<string|null>(null); const [assistantMessages,setAssistantMessages]=useState<AssistantMessage[]>([]); const [assistantInput,setAssistantInput]=useState(''); const [assistantPendingAction,setAssistantPendingAction]=useState<AssistantAction|null>(null); const [assistantLoading,setAssistantLoading]=useState(false); const [assistantApplying,setAssistantApplying]=useState(false); const [assistantError,setAssistantError]=useState('');
  const [contextInput,setContextInput]=useState<ContextInput>(emptyInput); const [linkDraft,setLinkDraft]=useState(''); const [goalQuestion,setGoalQuestion]=useState(''); const [goalPatch,setGoalPatch]=useState<any>(null); const [stageQuestion,setStageQuestion]=useState(''); const [stagePatch,setStagePatch]=useState<any>(null); const [questionAnswers,setQuestionAnswers]=useState<Record<string,string>>({}); const [questionGenLoading,setQuestionGenLoading]=useState(false); const [answerLoadingId,setAnswerLoadingId]=useState<string|null>(null); const [documents,setDocuments]=useState<any[]>([]); const [links,setLinks]=useState<any[]>([]); const [knowledge,setKnowledge]=useState<any>(null); const [thinking,setThinking]=useState(false); const [contextReady,setContextReady]=useState(false); const [contextArtifactVersion,setContextArtifactVersion]=useState<number|null>(null); const [problemDraft,setProblemDraft]=useState<any>({main_problem:'',user_pains:[],business_pains:[],root_causes:[],consequences_if_not_solved:[],evidence_signals:[],problem_statement:'',assumptions:[],missing_information:[],clarifying_questions:[],ai_chat_history:[],versions:[],status:'draft',source_context_version:0,problem_handoff:{},source_trace:[],context_readiness:{}}); const [problemPatch,setProblemPatch]=useState<any>(null); const [problemChat,setProblemChat]=useState('')
  const current=tabs.find(t=>t.type===active)
  const ensureRuntimeReady = async () => {
    try {
      const status = await api<any>('/runtime/status')
      if (!status?.llm?.ready_for_generation) {
        throw new ApiError(400, status?.llm?.human_message || 'LLM не готова к генерации', status?.llm)
      }
    } catch (e) {
      if (e instanceof ApiError) throw e
      throw new ApiError(0, 'Backend недоступен. Запустите backend на порту 8000 или проверьте VITE_API_URL.')
    }
  }

  const loadCompletion=async()=>{setCmp(await api<any>(`/projects/${projectId}/completion`).catch(()=>null)); const arts=await api<any[]>(`/projects/${projectId}/artifacts`).catch(()=>[]); const p:Record<string,any>={}; arts.forEach(a=>p[a.artifact_type]=a.structured_content?.pipeline_meta||{status:(a.content||'').trim()?'ready':'empty',version:a.version,updated_at:a.updated_at,source_artifacts:[],source_versions:{}}); setPipeline(p)}
  const load=async()=>{try{setProject(await api<Project>(`/projects/${projectId}`)); await loadCompletion()}catch{setMsg('Проект не найден')}}
  const loadAssistantSession=async()=>{
    if(!projectId) return
    try{
      const sessions=await assistantApi.listSessions(projectId)
      const latest=sessions.sessions?.[0]
      if(!latest) return
      setAssistantSessionId(latest.id)
      const history=await assistantApi.listMessages(projectId, latest.id)
      setAssistantMessages(history.messages||[])
    }catch(e:any){
      setAssistantError(e?.message||'Не удалось загрузить историю AI-чата')
    }
  }
  const sendAssistantMessage=async(message?:string)=>{
    if(!projectId) return
    const text=(message ?? assistantInput).trim()
    if(!text) return
    try{
      setAssistantLoading(true)
      setAssistantError('')
      const response=await assistantApi.sendMessage(projectId,{
        message:text,
        session_id:assistantSessionId,
        artifact_type:active,
        context:{active_stage:active, artifact_version:ver, project_name:project?.project_name}
      })
      setAssistantSessionId(response.session_id)
      setAssistantMessages(prev=>[...prev,response.user_message,response.assistant_message])
      setAssistantPendingAction(response.action||null)
      setAssistantInput('')
      if(response.errors?.length) setAssistantError(response.errors.join('\n'))
    }catch(e:any){
      setAssistantError(e?.message||'Ошибка AI-чата')
    }finally{
      setAssistantLoading(false)
    }
  }
  const applyAssistantPatch=async()=>{
    if(!projectId || !assistantSessionId || !assistantPendingAction){
      setAssistantError('Нет подготовленного patch для применения.')
      return
    }
    try{
      setAssistantApplying(true)
      setAssistantError('')
      const response=await assistantApi.applyPatch(projectId,{session_id:assistantSessionId,action_id:assistantPendingAction.id})
      const target=response.artifact.artifact_type
      setAssistantPendingAction(response.action)
      setActive(target)
      await loadArtifact(target)
      await loadCompletion()
      setMsg('Patch применён в артефакт после preview')
    }catch(e:any){
      setAssistantError(e?.message||'Ошибка применения patch')
    }finally{
      setAssistantApplying(false)
    }
  }
  const handleAssistantSuggestedAction=async(action:SuggestedActionKey)=>{
    if(action==='apply'){ await applyAssistantPatch(); return }
    if(action==='open_stage'){ setActive(assistantPendingAction?.target_artifact_type || active); return }
    if(action==='show_sources'){ setActive('CONTEXT'); return }
    if(action==='ask_questions'){ await sendAssistantMessage(`Задай уточняющие вопросы для этапа ${humanStage[active] || active}.`); return }
    if(action==='quality_check'){ await validate(); return }
    if(action==='export_docx'){ window.open(`http://localhost:8000/api/projects/${projectId}/export/docx`,'_blank') }
  }
  const loadStageQuestions=async()=>{try{await ensureRuntimeReady(); const r=await api<any>(`/projects/${projectId}/stage/${active}/questions`,{method:'POST'}); if(active==='PROBLEM') setProblemDraft((p:any)=>({...p, clarifying_questions:r.questions||[]})); else setStructured((st:any)=>({...st, ai_questions:r.questions||[]})); const mapped:Record<string,string>={}; (Array.isArray(r.questions)?r.questions:[]).forEach((q:any,i:number)=>{const id=(typeof q==='string'?`q_${i}`:q.id); mapped[id]=typeof q==='string'?'':(q.answer||'')}); setQuestionAnswers(prev=>({...prev,...mapped})); return r}catch(e:any){throw new Error(e?.message||'Не удалось сгенерировать вопросы')}}
  const regenerateStageQuestions=async()=>{try{setQuestionGenLoading(true); await loadStageQuestions(); setMsg('Дополнительные вопросы сгенерированы')}catch(e:any){setMsg(e?.message||'Ошибка генерации вопросов')}finally{setQuestionGenLoading(false)}}
  const applyContextSnapshot=(artifact:any)=>{
    const sc=artifact?.structured_content||{}
    const ci={...emptyInput,...(sc?.context_input||{})}
    setContextInput({...ci,product_goal:ci.product_goal||ci.initiative_goal||'',business_process_owner:ci.business_process_owner||ci.process_owner||'',discovery_responsible:ci.discovery_responsible||ci.discovery_owner||''})
    setDocuments(sc?.uploaded_files||sc?.documents||[])
    setLinks(sc?.links||[])
    setKnowledge(sc?.extracted_knowledge||null)
    setContextArtifactVersion(artifact?.version??null)
  }
  const loadLatestContextSnapshot=async()=>{
    const ctx=await api<any>(`/projects/${projectId}/artifacts/CONTEXT`).catch(()=>null)
    if(ctx) applyContextSnapshot(ctx)
    return ctx
  }
  const loadArtifact=async(type:ArtifactType)=>{
    try{
      const a=await api<any>(`/projects/${projectId}/artifacts/${type}`)
      setContent(a.rendered_html||a.content||'')
      setRichJson(a.rich_content_json||null)
      setStructured(a.structured_content||{})
      setVer(a.version)
      setUpdated(a.updated_at)
      if(type==='CONTEXT'){
        applyContextSnapshot(a)
        setContextReady(true)
      }
      if(type==='PROBLEM'){
        await loadLatestContextSnapshot()
        const sc=a.structured_content||{}
        const qs=(sc.ai_questions || sc.clarifying_questions || [])
        setProblemDraft((prev:any)=>({...prev,...sc, clarifying_questions: Array.isArray(qs)&&qs.length?qs:(prev.clarifying_questions||[]), ai_answers:Array.isArray(sc.ai_answers)&&sc.ai_answers.length?sc.ai_answers:(prev.ai_answers||[])}))
        const mapped:Record<string,string>={}
        ;(Array.isArray(qs)?qs:[]).forEach((q:any,i:number)=>{const id=(typeof q==='string'?`q_${i}`:q.id); mapped[id]=typeof q==='string'?'':(q.answer||'')})
        setQuestionAnswers(prev=>({...mapped,...prev}))
      }
      if(type==='GOAL'){
        setGoalDraft((a.structured_content||{}).aiDrafts||null)
      }
    }catch{
      setContent('')
      setRichJson(null)
      setStructured({})
      setVer(null)
      setUpdated('')
      if(type==='CONTEXT'){
        setContextInput(emptyInput)
        setDocuments([])
        setLinks([])
        setKnowledge(null)
        setContextArtifactVersion(null)
        setContextReady(true)
        try{
          const created=await api<any>(`/projects/${projectId}/artifacts/CONTEXT`,{method:'PUT',body:JSON.stringify({content:'',structured_content:{context_input:emptyInput,links:[],uploaded_files:[],extracted_knowledge:null,coverage:{},readiness:null,source_trace:[],problem_handoff:{},knowledge_coverage:{},indexing_status:'idle'}})})
          setContextArtifactVersion(created.version)
        }catch{}
      }
      if(type==='PROBLEM'){
        await loadLatestContextSnapshot()
      }
    }
  }
  useEffect(()=>{load(); loadAssistantSession(); if(projectId) localStorage.setItem('lastOpenedProjectId', projectId)},[projectId]);
  useEffect(()=>{const st = searchParams.get('stage') as ArtifactType | null; if(st && tabs.some(t=>t.type===st)) setActive(st)},[searchParams]);
  useEffect(()=>{loadArtifact(active); loadStageQuestions(); if(projectId) navigate(`/projects/${projectId}?stage=${active}`, { replace:true })},[active,projectId])




  const markDependentsStale=async(changed:ArtifactType, changedVersion:number)=>{try{const idx=stageOrder.indexOf(changed); if(idx<0) return; const dependents=stageOrder.slice(idx+1); for(const dep of dependents){const art=await api<any>(`/projects/${projectId}/artifacts/${dep}`).catch(()=>null); if(!art) continue; const sc=art.structured_content||{}; const meta=sc.pipeline_meta||{status:'draft',source_artifacts:[],source_versions:{},generated_at:null}; const nextMeta={...meta,status:'stale',source_artifacts:[...(meta.source_artifacts||[]),changed].filter((v:any,i:number,a:any[])=>a.indexOf(v)===i),source_versions:{...(meta.source_versions||{}),[changed]:changedVersion},updated_at:new Date().toISOString()}; await api<any>(`/projects/${projectId}/artifacts/${dep}`,{method:'PUT',body:JSON.stringify({content:art.content||'',structured_content:{...sc,pipeline_meta:nextMeta},rich_content_json:art.rich_content_json||null,rendered_html:art.rendered_html||null})})}
  }catch{}}

  const save=async()=>{try{setSaving('saving');const baseMeta={stage:active,status:'manually_edited',source_artifacts:stageOrder.slice(0,Math.max(0,stageOrder.indexOf(active))),source_versions:{},version:ver||0,updated_at:new Date().toISOString(),generated_at:null}; const payload=active==='GOAL'?{content:smartToText(goalData),structured_content:{...goalData,pipeline_meta:baseMeta},rich_content_json:richJson,rendered_html:content}:active==='CONTEXT'?{content:'',structured_content:{...buildContextPayload(),pipeline_meta:baseMeta},rich_content_json:null,rendered_html:null}:{content,structured_content:{pipeline_meta:baseMeta},rich_content_json:richJson,rendered_html:content}; const a=await api<any>(`/projects/${projectId}/artifacts/${active}`,{method:'PUT',body:JSON.stringify(payload)});setVer(a.version);setUpdated(a.updated_at);setMsg('Сохранено');setSaving('saved'); await markDependentsStale(active,a.version); await loadCompletion()}catch{setMsg('Ошибка сохранения');setSaving('error')}}
  const gen=async()=>{try{setBusy(true);await ensureRuntimeReady();const a=await api<any>(`/projects/${projectId}/generate/${active}`,{method:'POST'});setContent(a.content);setStructured({});setVer(a.version);setUpdated(a.updated_at);setMsg('Генерация завершена');await loadCompletion()}catch(e:any){setMsg(e?.message||'Ошибка сохранения')}finally{setBusy(false)}}
  const validate=async()=>{try{setBusy(true);await ensureRuntimeReady();await api<any>(`/projects/${projectId}/validate`,{method:'POST'});setMsg('Сохранено');await loadCompletion()}catch(e:any){setMsg(e?.message||'Ошибка сохранения')}finally{setBusy(false)}}
  useEffect(()=>{if(active==='GOAL' || active==='CONTEXT' || active==='PROBLEM') return; if(!content) return; const t=setTimeout(()=>{save()},2000); return ()=>clearTimeout(t)},[content])
  useEffect(()=>{if(active!=='PROBLEM') return; const t=setTimeout(()=>{saveProblem()},900); return ()=>clearTimeout(t)},[problemDraft])
  useEffect(()=>{if(active!=='CONTEXT' || !contextReady) return; const t=setTimeout(()=>{saveContextInput()},800); return ()=>clearTimeout(t)},[contextInput,documents,links,knowledge,contextReady])


  const buildContextPayload=(overrides:any={})=>{
    const nextDocuments = overrides.documents ?? documents
    const nextLinks = overrides.links ?? links
    const nextKnowledge = overrides.knowledge ?? knowledge
    const nextStructured = overrides.structured ?? structured
    return ({
    initiative_name: contextInput.initiative_name,
    short_description: contextInput.short_description,
    initiative_goal: contextInput.product_goal || contextInput.initiative_goal,
    product_goal: contextInput.product_goal || contextInput.initiative_goal,
    business_domain: contextInput.business_domain,
    process_owner: contextInput.business_process_owner || contextInput.process_owner,
    discovery_owner: contextInput.discovery_responsible || contextInput.discovery_owner,
    business_process_owner: contextInput.business_process_owner || contextInput.process_owner,
    discovery_responsible: contextInput.discovery_responsible || contextInput.discovery_owner,
    related_processes: contextInput.related_processes,
    related_systems: contextInput.related_systems,
    context_input: {
      ...contextInput,
      product_goal: contextInput.product_goal || contextInput.initiative_goal,
      business_process_owner: contextInput.business_process_owner || contextInput.process_owner,
      discovery_responsible: contextInput.discovery_responsible || contextInput.discovery_owner,
      initiative_goal: contextInput.product_goal || contextInput.initiative_goal,
      process_owner: contextInput.business_process_owner || contextInput.process_owner,
      discovery_owner: contextInput.discovery_responsible || contextInput.discovery_owner
    },
    links: nextLinks,
    uploaded_files: nextDocuments,
    documents: nextDocuments,
    extracted_knowledge: nextKnowledge,
    problem_handoff: nextStructured?.problem_handoff || nextKnowledge?.problem_handoff || {},
    source_trace: nextStructured?.source_trace || nextKnowledge?.source_trace || [],
    coverage: nextStructured?.coverage || nextKnowledge?.coverage || nextKnowledge?.покрытие || {},
    readiness: nextStructured?.readiness || nextKnowledge?.readiness || null,
    knowledge_coverage: nextStructured?.coverage || nextKnowledge?.coverage || nextKnowledge?.покрытие || {},
    indexing_status: nextStructured?.indexing_status || 'idle',
    indexed_at: nextStructured?.indexed_at || null,
    knowledge_history: nextStructured?.knowledge_history||[]
  })}

  const saveContextInput=async(overrides:any={})=>{try{if(!projectId) return; setSaving('saving'); const a=await api<any>(`/projects/${projectId}/artifacts/CONTEXT`,{method:'PUT',body:JSON.stringify({content:'',structured_content:buildContextPayload(overrides)})}); setVer(a.version); setUpdated(a.updated_at); setStructured(a.structured_content||{}); setContextArtifactVersion(a.version); setSaving('saved'); return a}catch{setSaving('error'); setMsg('Ошибка сохранения контекста')}}
  const runContextAnalyze=async()=>{try{setThinking(true); await ensureRuntimeReady(); const indexingDocs=(Array.isArray(documents)?documents:[]).map((d:any)=>({...d,status:'indexing',updatedAt:new Date().toISOString()})); setDocuments(indexingDocs); const r=await api<any>(`/projects/${projectId}/context/analyze`,{method:'POST',body:JSON.stringify({context_input:contextInput,documents:indexingDocs,links})}); const now=new Date().toISOString(); const extracted=r.extracted_knowledge; const trace=Array.isArray(r.source_trace)?r.source_trace:(Array.isArray(extracted?.source_trace)?extracted.source_trace:[]); const coverage=r.coverage||extracted?.coverage||{}; const readiness=r.readiness||extracted?.readiness||null; const handoff=r.problem_handoff||extracted?.problem_handoff||{}; const nextDocs=indexingDocs.map((d:any)=>{const tr=trace.find((x:any)=>x.source_type==='document'&&String(x.source_id)===String(d.id)); const extractionStatus=d.text_extraction_status; const failedStatus=['failed','unsupported','empty'].includes(extractionStatus)?(extractionStatus==='unsupported'?'unsupported':extractionStatus==='empty'?'empty':'error'):'uploaded'; return {...d,status:tr?.used?'ready':failedStatus,ai_status:tr?.used?'проиндексирован':'требует текста',updatedAt:now}}); const nextHistory=[...(structured?.knowledge_history||[]),{created_at:now,extracted_knowledge:extracted,documents:nextDocs,links,source_trace:trace,coverage,readiness,problem_handoff:handoff}].slice(-30); const nextStructured={...structured,indexing_status:r.indexing_status||'completed',indexed_at:now,source_trace:trace,coverage,readiness,problem_handoff:handoff,knowledge_history:nextHistory}; setDocuments(nextDocs); setKnowledge(extracted); setStructured(nextStructured); setMsg('Индексация знаний завершена'); await saveContextInput({documents:nextDocs,knowledge:extracted,structured:nextStructured})}catch(e:any){const errored=(Array.isArray(documents)?documents:[]).map((d:any)=>d.status==='indexing'?{...d,status:'error',errorMessage:e?.message||'Ошибка индексации'}:d); setDocuments(errored); setMsg(e?.message||'Ошибка индексации')}finally{setThinking(false)}}

  const uploadContextFiles=async(e:any)=>{
    const files=Array.from(e.target.files||[]) as globalThis.File[]
    e.target.value=''
    if(!files.length) return
    const existingNames=new Set((documents||[]).map((d:any)=>String(d.fileName||d.name||d.title||'').toLowerCase()))
    const accepted:globalThis.File[]=[]
    const rejected:any[]=[]
    for(const f of files){
      const ext=extensionOf(f.name)
      if(existingNames.has(f.name.toLowerCase())){rejected.push(normalizeContextSource({fileName:f.name,name:f.name,size:f.size,status:'error',errorMessage:'Файл уже добавлен'},projectId,'document')); continue}
      if(!CONTEXT_FILE_EXTENSIONS.includes(ext)){rejected.push(normalizeContextSource({fileName:f.name,name:f.name,size:f.size,status:'error',text_extraction_status:'unsupported',errorMessage:`Неподдерживаемый формат: ${ext||'unknown'}`},projectId,'document')); continue}
      if(f.size>MAX_CONTEXT_FILE_SIZE){rejected.push(normalizeContextSource({fileName:f.name,name:f.name,size:f.size,status:'error',text_extraction_status:'failed',errorMessage:'Файл слишком большой. Максимальный размер: 15 МБ.'},projectId,'document')); continue}
      accepted.push(f)
    }
    let uploaded:any[]=[]
    if(accepted.length){
      try{
        setSaving('saving')
        const form=new FormData()
        accepted.forEach(f=>form.append('files',f))
        const r=await apiForm<any>(`/projects/${projectId}/context/sources/upload`,form)
        uploaded=(r.sources||[]).map((s:any)=>normalizeContextSource(s,projectId,'document'))
      }catch(err:any){
        uploaded=accepted.map(f=>normalizeContextSource({fileName:f.name,name:f.name,size:f.size,status:'error',errorMessage:err?.message||'Ошибка загрузки файла'},projectId,'document'))
      }
    }
    const next=[...(documents||[]),...uploaded,...rejected]
    const nextStructured={...structured,indexing_status:'requires_update'}
    setDocuments(next)
    setStructured(nextStructured)
    await saveContextInput({documents:next,structured:nextStructured})
    setMsg(rejected.length?`Добавлены файлы, часть отклонена: ${rejected.length}`:'Файлы добавлены. Обновите контекст для анализа.')
  }


  const removeDocument = async(index:number)=>{if(!confirm('Удалить файл из контекста?')) return; const next=(documents||[]).filter((_:any,i:number)=>i!==index); const nextStructured={...structured,indexing_status:'requires_update'}; try{setDocuments(next); setStructured(nextStructured); await saveContextInput({documents:next,structured:nextStructured}); setMsg('Файл удалён. Контекст требует обновления.')}catch{setMsg('Ошибка удаления файла')}}
  const removeLink = async(index:number)=>{if(!confirm('Удалить ссылку из контекста?')) return; const next=(links||[]).filter((_:any,i:number)=>i!==index); const nextStructured={...structured,indexing_status:'requires_update'}; try{setLinks(next); setStructured(nextStructured); await saveContextInput({links:next,structured:nextStructured}); setMsg('Ссылка удалена. Контекст требует обновления.')}catch{setMsg('Ошибка удаления ссылки')}}
  const addLink = ()=>{const v=linkDraft.trim(); if(!v) return; try{new URL(v)}catch{setMsg('Введите корректный URL ссылки'); return} const duplicate=(links||[]).some((l:any)=>String(l?.url||l).trim().toLowerCase()===v.toLowerCase()); if(duplicate){setMsg('Такая ссылка уже добавлена'); return} const next=[...(links||[]),normalizeContextSource({url:v,type:detectLinkType(v),status:'uploaded'},projectId,'link') as any]; setLinks(next); setStructured((s:any)=>({...s,indexing_status:'requires_update'})); setLinkDraft('')}

  const normalizeProblemStatement=(value:string)=>{
    const text=(value||'').trim()
    if(!text) return ''
    if(/^\s*\d+[.)]\s+/m.test(text)) return text
    const chunks=text.split(/(?<=[.!?])\s+/).map(s=>s.trim()).filter(Boolean)
    if(chunks.length<=1) return `1. ${text}`
    return chunks.map((item,idx)=>`${idx+1}. ${item}`).join('\n')
  }


  const generateProblem=async()=>{
    try{
      setThinking(true)
      const questionsWithAnswers = (problemDraft.clarifying_questions || []).map((q:any, i:number)=>{
        if(typeof q === 'string'){
          const id = `q_${i}`
          return { id, text: q, answer: (questionAnswers[id] || '').trim() }
        }
        const id = q?.id || `q_${i}`
        return { ...q, id, answer: (questionAnswers[id] ?? q?.answer ?? '').trim() }
      })
      const nextDraft = { ...problemDraft, ai_questions: questionsWithAnswers, clarifying_questions: questionsWithAnswers }
      await api<any>(`/projects/${projectId}/artifacts/PROBLEM`,{method:'PUT',body:JSON.stringify({content:nextDraft.problem_statement||nextDraft.main_problem||'',structured_content:nextDraft})})
      await ensureRuntimeReady(); const r=await api<any>(`/projects/${projectId}/problem/generate`,{method:'POST'})
      setProblemDraft((prev:any)=>{
        const incoming = r?.structured_content || {}
        return {
          ...prev,
          ...nextDraft,
          ...incoming,
          main_problem: (incoming.main_problem ?? '').trim() ? incoming.main_problem : (prev.main_problem || nextDraft.main_problem || ''),
          problem_statement: (incoming.problem_statement ?? '').trim() ? incoming.problem_statement : (prev.problem_statement || nextDraft.problem_statement || ''),
          user_pains: Array.isArray(incoming.user_pains) ? incoming.user_pains : (prev.user_pains || []),
          business_pains: Array.isArray(incoming.business_pains) ? incoming.business_pains : (prev.business_pains || []),
          ai_answers: Array.isArray(incoming.ai_answers) ? incoming.ai_answers : (prev.ai_answers || []),
          clarifying_questions: Array.isArray(incoming.clarifying_questions) && incoming.clarifying_questions.length ? incoming.clarifying_questions : (prev.clarifying_questions || nextDraft.clarifying_questions || []),
          ai_questions: Array.isArray(incoming.ai_questions) && incoming.ai_questions.length ? incoming.ai_questions : (prev.ai_questions || nextDraft.ai_questions || [])
        }
      })
      setProblemDraft((prev:any)=>({...prev, problem_statement: normalizeProblemStatement(prev.problem_statement||'')}))
      setMsg('Черновик проблемы сгенерирован на основе контекста и ответов')
    }catch{
      setMsg('Ошибка генерации проблемы')
    }finally{
      setThinking(false)
    }
  }
  const saveProblem=async(status?:string)=>{try{setSaving('saving'); const next={...problemDraft,status:status||problemDraft.status}; const a=await api<any>(`/projects/${projectId}/artifacts/PROBLEM`,{method:'PUT',body:JSON.stringify({content:next.problem_statement||next.main_problem||'',structured_content:next})}); setProblemDraft(a.structured_content||next); setSaving('saved'); setMsg('Проблема сохранена')}catch{setSaving('error'); setMsg('Ошибка сохранения проблемы')}}
  const askProblem=async()=>{try{setThinking(true); const r=await api<any>(`/projects/${projectId}/problem/ask`,{method:'POST',body:JSON.stringify({message:problemChat,draft:problemDraft})}); setProblemPatch(r.patch); setProblemDraft({...problemDraft, ai_chat_history:[...(problemDraft.ai_chat_history||[]),{role:'user',text:problemChat},{role:'assistant',text:r.assistant_message}]}); setProblemChat('')}catch{setMsg('Ошибка AI уточнения')}finally{setThinking(false)}}
  const applyPatch=async()=>{if(!problemPatch) return; try{const r=await api<any>(`/projects/${projectId}/problem/apply-patch`,{method:'POST',body:JSON.stringify({patch:{...problemDraft,...problemPatch},status:'needs_clarification'})}); setProblemDraft(r.structured_content||problemDraft); setProblemPatch(null); setMsg('Изменения применены')}catch{setMsg('Ошибка применения изменений')}}

  const smartToText=(goal:GoalDraft)=>`Цель инициативы: ${goal.title}\nПроблема: ${goal.businessProblem}\nЖелаемый результат: ${goal.desiredOutcome}\nKPI: ${(goal.successMetrics||[]).map(m=>`${m.metric}: ${m.currentValue||'—'} -> ${m.targetValue}`).join('; ')}`
  const toArray=(v:any)=>Array.isArray(v)?v:[]
  const updateGoal=(patch:Partial<GoalDraft>)=>setStructured({...goalData,...patch,updatedAt:new Date().toISOString()})
  const goalData:GoalDraft = { ...emptyGoal(), ...(structured||{}) }
  const addListItem=(key:'nonGoals'|'assumptions'|'risks'|'constraints'|'stakeholders',val:string)=>{ if(!val.trim()) return; updateGoal({[key]:[...toArray(goalData[key]),val.trim()] } as any) }
  const removeListItem=(key:'nonGoals'|'assumptions'|'risks'|'constraints'|'stakeholders',idx:number)=> updateGoal({[key]:toArray(goalData[key]).filter((_:any,i:number)=>i!==idx)} as any)


  const runAiAction=async(key:string,fn:()=>Promise<void>)=>{try{setAiActionLoading(key); setMsg(''); await fn(); setAiActionStatus(s=>({...s,[key]:'success'}))}catch(e:any){setAiActionStatus(s=>({...s,[key]:'error'})); setMsg(e?.message||'Ошибка AI действия')}finally{setAiActionLoading(null)}}
  const aiActionsByStage:Record<string,{key:string;label:string;enabled:boolean;onClick?:()=>void}[]>={
    CONTEXT:[{key:'ctx_refresh',label:thinking?'Обновляем...':'Обновить контекст',enabled:!thinking,onClick:()=>runAiAction('ctx_refresh',runContextAnalyze)}],
    PROBLEM:[{key:'pr_gen',label:'Сгенерировать проблему из контекста',enabled:true,onClick:()=>runAiAction('pr_gen',generateProblem)},{key:'pr_ask',label:'Задать уточняющие вопросы',enabled:true,onClick:()=>runAiAction('pr_ask',askProblem)},{key:'pr_root',label:'Найти корневые причины',enabled:true,onClick:()=>runAiAction('pr_root',generateProblem)},{key:'pr_upd',label:'Обновить по контексту',enabled:true,onClick:()=>runAiAction('pr_upd',generateProblem)}],
    GOAL:[{key:'goal_gen',label:'Сгенерировать цели из контекста и проблемы',enabled:true,onClick:()=>runAiAction('goal_gen',async()=>{const r=await api<any>(`/projects/${projectId}/goal/generate`,{method:'POST'}); setGoalDraft(r.draft||null); if(r.warning) setMsg(r.warning); await loadArtifact('GOAL')})},{key:'goal_kpi',label:'Предложить KPI',enabled:false},{key:'goal_smart',label:'Проверить SMART',enabled:false},{key:'goal_contra',label:'Найти противоречия',enabled:false},{key:'goal_decomp',label:'Декомпозировать цель',enabled:false}],
    BUSINESS_EFFECT:[{key:'be_gen',label:'Сгенерировать бизнес-эффект',enabled:true,onClick:()=>runAiAction('be_gen',gen)},{key:'be_metric',label:'Предложить метрики',enabled:false},{key:'be_eval',label:'Оценить FTE / риски / доход',enabled:false}],
    AS_IS:[{key:'as_gen',label:'Сгенерировать AS IS',enabled:true,onClick:()=>runAiAction('as_gen',gen)},{key:'as_manual',label:'Выявить ручные операции',enabled:false},{key:'as_bottleneck',label:'Найти узкие места',enabled:false}],
    TO_BE:[{key:'tb_gen',label:'Сгенерировать TO BE',enabled:true,onClick:()=>runAiAction('tb_gen',gen)},{key:'tb_auto',label:'Предложить варианты автоматизации',enabled:false},{key:'tb_cmp',label:'Сравнить варианты',enabled:false}],
    USE_CASES:[{key:'uc_gen',label:'Сгенерировать сценарии',enabled:true,onClick:()=>runAiAction('uc_gen',gen)},{key:'uc_neg',label:'Добавить негативные сценарии',enabled:false},{key:'uc_edge',label:'Добавить edge cases',enabled:false}],
    FUNCTIONAL_REQUIREMENTS:[{key:'req_gen',label:'Сгенерировать требования',enabled:true,onClick:()=>runAiAction('req_gen',gen)},{key:'req_nfr',label:'Сгенерировать NFR',enabled:false},{key:'req_check',label:'Проверить полноту требований',enabled:true,onClick:()=>runAiAction('req_check',validate)}],
    RISKS:[{key:'risk_gen',label:'Сгенерировать риски',enabled:true,onClick:()=>runAiAction('risk_gen',gen)},{key:'risk_dep',label:'Найти зависимости',enabled:false},{key:'risk_rb',label:'Сформировать rollback',enabled:false}],
    FINAL_BT:[{key:'bt_build',label:'Собрать финальный БТ',enabled:true,onClick:()=>runAiAction('bt_build',gen)},{key:'bt_empty',label:'Проверить пустые разделы',enabled:true,onClick:()=>runAiAction('bt_empty',validate)},{key:'bt_docx',label:'Экспортировать DOCX',enabled:true,onClick:()=>window.open(`http://localhost:8000/api/projects/${projectId}/export/docx`,'_blank')}]
  }


  const applyGoalOption=(opt:any,mode:'select'|'merge')=>{if(!opt) return; const next:any={...goalData}; if(mode==='select'){next.title=opt.title||''; next.businessProblem=opt.description||next.businessProblem; next.desiredOutcome=opt.why_relevant||next.desiredOutcome; next.successMetrics=(opt.suggested_kpis||[]).map((m:string)=>({metric:m,targetValue:''})); next.nonGoals=opt.non_goals||[]; next.assumptions=opt.assumptions||[]} else {next.successMetrics=[...(next.successMetrics||[]),...(opt.suggested_kpis||[]).map((m:string)=>({metric:m,targetValue:''}))]; next.nonGoals=[...(next.nonGoals||[]),...(opt.non_goals||[])]; next.assumptions=[...(next.assumptions||[]),...(opt.assumptions||[])]} updateGoal(next)}
  const applyRecommendedGoal=()=>{const r=goalDraft?.recommended_goal; if(!r) return; updateGoal({...goalData,title:r.title||goalData.title,businessProblem:r.business_problem||goalData.businessProblem,desiredOutcome:r.desired_outcome||goalData.desiredOutcome,successMetrics:(r.success_metrics||[]).map((m:any)=>typeof m==='string'?{metric:m,targetValue:''}:m),nonGoals:r.non_goals||goalData.nonGoals,assumptions:r.assumptions||goalData.assumptions,risks:r.risks||goalData.risks,smartAnalysis:goalDraft?.smart_analysis||goalData.smartAnalysis})}


  const askGoal=async()=>{if(!goalQuestion.trim()) return; const patch={aiQuestions:[...(goalData.aiQuestions||[]),`Уточнение: ${goalQuestion}`], assumptions:[...(goalData.assumptions||[]),'Требуется подтверждение по ответу пользователя']}; setGoalPatch(patch); setGoalQuestion('')}
  const applyGoalPatch=()=>{if(!goalPatch) return; updateGoal({...goalData,...goalPatch}); setGoalPatch(null)}
  const addMetric=()=>updateGoal({successMetrics:[...(goalData.successMetrics||[]),{metric:'',currentValue:'',targetValue:'',measurement:'',dataSource:''}]})

  const goalDependents:ArtifactType[]=['BUSINESS_EFFECT','AS_IS','TO_BE','USE_CASES','FUNCTIONAL_REQUIREMENTS','RISKS','FINAL_BT']
  const showGoalNotice=goalDependents.includes(active) && (pipeline[active]?.source_versions?.GOAL || pipeline[active]?.status==='stale')

  const askStageQuestion=async()=>{if(!stageQuestion.trim()) return; try{setThinking(true); const r=await api<any>(`/projects/${projectId}/stage/${active}/ask`,{method:'POST',body:JSON.stringify({message:stageQuestion})}); setStagePatch(r.patch); setStageQuestion(''); setMsg('AI сформировал предложения')}catch(e:any){setMsg(e?.message||'Ошибка AI вопроса')}finally{setThinking(false)}}

  const answerQuestion=async(q:any)=>{const ans=(questionAnswers[q.id]||'').trim(); if(!ans) return; try{setAnswerLoadingId(q.id); const qText=safeText(q?.text||q); setProblemDraft((prev:any)=>{const history=Array.isArray(prev.ai_answers)?prev.ai_answers:[]; const next=[...history]; const idx=next.findIndex((x:any)=>safeText(x?.question)===qText); const row={question:qText,answer:ans,updated_at:new Date().toISOString()}; if(idx>=0) next[idx]={...next[idx],...row}; else next.unshift(row); return {...prev, ai_answers:next};}); const r=await api<any>(`/projects/${projectId}/stage/${active}/ask`,{method:'POST',body:JSON.stringify({question_id:q.id,message:ans})}); setStagePatch(r.patch); await loadArtifact(active); setMsg('Ответ сохранен и учтен для генерации')}catch(e:any){setMsg(e?.message||'Ошибка ответа')}finally{setAnswerLoadingId(null)}}

  const applyStagePatch=async()=>{if(!stagePatch) return; try{setThinking(true); const r=await api<any>(`/projects/${projectId}/stage/${active}/apply-patch`,{method:'POST',body:JSON.stringify({patch:stagePatch})}); setStructured(r.structured_content||structured); setStagePatch(null); setMsg('AI patch применен')}catch(e:any){setMsg(e?.message||'Ошибка применения patch')}finally{setThinking(false)}}
  const sourceTrace=((structured?.source_trace || knowledge?.source_trace || []) as any[])
  const contextCoverage=structured?.coverage || knowledge?.coverage || knowledge?.покрытие || {}
  const contextReadiness=structured?.readiness || knowledge?.readiness || null
  const contextMissing=((knowledge?.missing_information || structured?.extracted_knowledge?.missing_information || []) as any[]).map(safeText).filter(Boolean)
  const problemHandoff=structured?.problem_handoff || knowledge?.problem_handoff || {}
  const manualFilled=Boolean((contextInput.short_description||contextInput.product_goal||contextInput.business_domain||contextInput.business_process_owner||contextInput.discovery_responsible||'').trim())
  const textSources=sourceTrace.filter((s:any)=>s.content_level && s.content_level!=='metadata_only').length
  const metadataOnly=sourceTrace.filter((s:any)=>s.content_level==='metadata_only').length
  const totalSources=(documents?.length||0)+(links?.length||0)
  const contextStatusLabel=(()=>{
    if(saving==='error') return 'Контекст: ошибка обновления · повторите попытку'
    if(!manualFilled && !documents.length && !links.length) return 'Контекст: не заполнен'
    if(structured?.indexing_status==='requires_update') return 'Контекст: требует обновления · источники изменены'
    if(thinking) return `Контекст: обновляется... · ${documents.length} документов · ${links.length} ссылок`
    if(totalSources>0 && !knowledge) return `Контекст: загружен · требуется обработка · ${documents.length} документов · ${links.length} ссылок`
    if(totalSources>0 && textSources===0 && metadataOnly>0) return `Контекст: частично обработан · файлы добавлены, но текст не извлечён · ${documents.length} документов · ${links.length} ссылок`
    if(textSources>0 && metadataOnly>0) return `Контекст: частично обработан · ${textSources} источников с текстом · ${metadataOnly} только с метаданными`
    if(textSources>0) return `Контекст: обработан · знания извлечены · ${textSources} источников с текстом · обновлено ${updated?new Date(updated).toLocaleString('ru-RU'):'—'}`
    return `Контекст: загружен · ${documents.length} документов · ${links.length} ссылок`
  })()
  const updateContextField=(key:string,value:string)=>{setContextInput((prev:any)=>({...prev,[key]:value})); setStructured((prev:any)=>({...prev,indexing_status:'requires_update'}))}
  const goProblemFromContext=()=>{
    const status=contextReadiness?.status
    if(status==='warning'&&!window.confirm('Готовность контекста средняя. Можно перейти к Problem, но анализ может потребовать уточнений. Перейти?')) return
    if(status==='blocked'&&!window.confirm('Контекст низкого качества: не хватает подтверждённых данных. Перейти к Problem всё равно?')) return
    setActive('PROBLEM')
  }

  if(!project) return <div className='ui-card'>Проект не найден</div>
  return <div className='workspace-single project-workspace-chat'>
    <aside className='project-workspace-nav'>
      <div className='ui-card page-section-gap'>
        <div className='chat-first-marker'>AI Discovery Chat — основная точка входа</div>
        <div className='top-progress'><div><span className='sub'>Общий прогресс: <b>{cmp?.completion_percent ?? 0}%</b></span><progress className='progress-native' value={cmp?.completion_percent ?? 0} max={100} /></div></div>
        <div className='ui-stage-tabs ui-stage-tabs--vertical'>{tabs.map(t=>{const st=(pipeline[t.type]?.status||'empty'); return <Button key={t.type} size='sm' variant='ghost' className={`ui-stage-tab ${active===t.type?'active':''}`} onClick={()=>setActive(t.type)}>{t.label}<span className={`pipe-dot ${st}`}/></Button>})}</div>{showGoalNotice && <div className='goal-notice'>Цель изменилась после последней генерации этого раздела. Рекомендуется обновить раздел.</div>}<AIActionBar actions={aiActionsByStage[active]||[]} loading={aiActionLoading}/>
      </div>
    </aside>

    <section className='project-workspace-main'>
      <div className='ui-card'>
        <div className='ui-actions ui-actions--between'>
          <div><h2 className='section-title-main'>{current?.label}</h2><p className='sub sub-reset'>{project.project_name} · В работе · Версия {ver??0} · Обновлено: {updated?new Date(updated).toLocaleString('ru-RU'):'—'}</p></div>
          <div className='ui-actions'><span className='sub'>Версия: {ver??0}</span><span className='sub'>Обновлено: {updated?new Date(updated).toLocaleString('ru-RU'):'—'}</span>{active!=='CONTEXT' && <Button variant='primary' size='sm' onClick={save}>Сохранить</Button>}{active!=='CONTEXT' && <Button variant='secondary' size='sm' onClick={gen} disabled={busy}>Сгенерировать</Button>}{active!=='CONTEXT' && <Button variant='secondary' size='sm' onClick={validate} disabled={busy}>Проверить</Button>}{active==='FINAL_BT' && <ButtonLink variant='icon' size='sm' href={`http://localhost:8000/api/projects/${projectId}/export/docx`}><Download size={16}/></ButtonLink>}{active!=='CONTEXT' && <Button variant='icon' size='sm' aria-label='Дополнительные действия'><MoreHorizontal size={16}/></Button>}</div>
        </div>

        <ErrorBoundary fallbackTitle='Ошибка рендера этапа'>{active==='CONTEXT' ? <ContextStage contextStatus={contextStatusLabel} onGoProblem={goProblemFromContext} sourceTrace={sourceTrace} contextInput={contextInput} onUpdateContextField={updateContextField} documents={Array.isArray(documents)?documents:[]} links={(Array.isArray(links))?links:[]} knowledge={knowledge} coverage={contextCoverage} readiness={contextReadiness} missingInformation={contextMissing} problemHandoff={problemHandoff} indexingStatus={structured?.indexing_status||'idle'} runContextAnalyze={runContextAnalyze} onUpload={uploadContextFiles} onDeleteDocument={removeDocument} onDeleteLink={removeLink} linkDraft={linkDraft} setLinkDraft={setLinkDraft} onAddLink={addLink} />: active==='PROBLEM' ? <div className='problem-workspace'>
          <div className='problem-left ui-card'><h4>Контекст для анализа</h4><div className='sub'>{contextInput.initiative_name}</div><div className='sub'>{contextInput.short_description}</div><div className='sub'>Готовность: {contextReadiness?.status ? `${contextReadiness.status} · ${contextReadiness.score ?? 0}%` : 'не рассчитана'}</div><div className='sub'>Процессы: {safeText((knowledge?.процессы||knowledge?.processes||[]).slice(0,5))}</div><div className='sub'>Системы: {safeText((knowledge?.системы||knowledge?.systems||[]).slice(0,5))}</div><div className='sub'>Роли: {safeText((knowledge?.роли||knowledge?.roles||[]).slice(0,5))}</div><div className='sub'>Context version: {contextArtifactVersion ?? '—'} · Problem source version: {problemDraft.source_context_version || 0}</div><Button variant='secondary' onClick={()=>loadLatestContextSnapshot()}>Обновить из контекста</Button>{problemDraft.source_context_version && contextArtifactVersion && problemDraft.source_context_version<contextArtifactVersion ? <div className='ui-card'><p className='sub'>Контекст изменился. Рекомендуется обновить анализ проблемы.</p><Button variant='secondary' onClick={generateProblem}>Обновить проблему по новому контексту</Button></div>:null}<div className='ui-card problem-answers-sticky'><h4 className='ai-answers-title'>Ответы пользователя</h4>{(problemDraft.ai_answers||[]).map((a:any,i:number)=><div key={`hist_${i}`} className='ai-answer-row'><div><b>В:</b> {safeText(a.question)}</div><div className='sub'><b>О:</b> {safeText(a.answer)}</div></div>)}{!(problemDraft.ai_answers||[]).length && <div className='sub'>Пока нет сохранённых ответов.</div>}<div className='sub'>История ответов не очищается при перегенерации вопросов.</div></div></div>
          <div className='problem-center ui-card'><h4>Формулировка проблемы</h4><label className='sub'>Ручная формулировка от PO</label><textarea className='ui-textarea' placeholder='В чём проблема?' value={problemDraft.main_problem||''} onChange={e=>setProblemDraft({...problemDraft,main_problem:e.target.value})}/><label className='sub'>Проблемы для БТ (AI, строгая нумерация)</label><textarea className='ui-textarea' value={problemDraft.problem_statement||''} onChange={e=>setProblemDraft({...problemDraft,problem_statement:e.target.value})}/><div className='ui-card-footer'><Button variant='primary' size='md' onClick={generateProblem} disabled={thinking}>{thinking?'Генерация...':'Сгенерировать'}</Button><Button variant='secondary' size='md' onClick={()=>saveProblem()}>Сохранить</Button><Button variant='soft' size='md' onClick={()=>saveProblem('ready')}>Принять как финальную проблему</Button><Button variant='ghost' size='md' onClick={()=>{const v=(problemDraft.versions||[]).slice(-1)[0]?.snapshot; if(v) setProblemDraft({...problemDraft,...v})}}>Вернуть предыдущую версию</Button></div><div className='sub'>Статус: {safeText(problemDraft.status||'draft')}</div></div>
          <div className='problem-right ui-card'><h4>AI уточняющие вопросы</h4><Button variant='soft' size='sm' fullWidth onClick={regenerateStageQuestions} disabled={questionGenLoading}>{questionGenLoading?'Генерация...':'Сгенерировать дополнительные вопросы'}</Button><div className='ai-sections'>{(problemDraft.clarifying_questions||[]).map((q:any,i:number)=>{const obj=typeof q==='string'?{id:`q_${i}`,text:q,answer:''}:q; return <div key={obj.id||i} className='ui-card ai-question-card'><b>Вопрос {i+1}</b><div className='sub'>{safeText(obj.text||obj)}</div><input className='ui-input' placeholder='Ваш ответ...' value={questionAnswers[obj.id] ?? obj.answer ?? ''} onChange={e=>setQuestionAnswers({...questionAnswers,[obj.id]:e.target.value})}/><div className='ui-actions'><Button variant='secondary' size='sm' fullWidth onClick={()=>answerQuestion(obj)} disabled={answerLoadingId===obj.id}>{answerLoadingId===obj.id?'Сохранение...':'Сохранить ответ'}</Button></div></div>})}{(problemDraft.ai_chat_history||[]).map((m:any,i:number)=><div key={i} className='ui-card'><b>{m.role==='user'?'Вы':'AI'}</b><div className='sub'>{safeText(m.text)}</div></div>)}</div>{stagePatch && <div className='ui-card'><div className='sub'>AI предлагает изменения.</div><div className='ui-card-footer'><Button variant='primary' size='sm' onClick={applyStagePatch}>Применить</Button><Button variant='secondary' onClick={()=>setStagePatch(null)}>Отклонить</Button></div></div>}</div>
        </div> : active==='GOAL' ? <div className='goal-screen'>
          <div className='ui-card'><h4>Источники для генерации цели</h4><div className='sub'>Контекст: {(contextInput.initiative_name||contextInput.short_description)?'заполнен':'не заполнен'} · Проблема: {(problemDraft.main_problem||problemDraft.problem_statement)?'заполнена':'не заполнена'}</div><div className='timeline'><span className='ui-badge progress'>Процессы: {((knowledge?.процессы||knowledge?.processes||[]) as any[]).length}</span><span className='ui-badge progress'>Системы: {((knowledge?.системы||knowledge?.systems||[]) as any[]).length}</span><span className='ui-badge progress'>Корневые причины: {((problemDraft.root_causes||[]) as any[]).length}</span></div></div>
          <div className='ui-card'><h4>Целевая формулировка</h4>
            <input className='ui-input' placeholder='Название цели' value={goalData.title||''} onChange={e=>updateGoal({title:e.target.value})}/>
            <textarea className='ui-textarea ui-textarea--lg' placeholder='Какую проблему решаем' value={goalData.businessProblem||''} onChange={e=>updateGoal({businessProblem:e.target.value})}/>
            <textarea className='ui-textarea ui-textarea--lg' placeholder='Какой результат хотим получить' value={goalData.desiredOutcome||''} onChange={e=>updateGoal({desiredOutcome:e.target.value})}/>
            <textarea className='ui-textarea ui-textarea--md' placeholder='Почему это важно бизнесу' value={goalData.businessImportance||''} onChange={e=>updateGoal({businessImportance:e.target.value})}/>
            <textarea className='ui-textarea ui-textarea--md' placeholder='Что произойдет, если ничего не делать' value={goalData.noActionImpact||''} onChange={e=>updateGoal({noActionImpact:e.target.value})}/>
            <textarea className='ui-textarea ui-textarea--md' placeholder='Что НЕ входит в scope' value={(goalData.nonGoals||[]).join('\n')} onChange={e=>updateGoal({nonGoals:e.target.value.split('\n').filter(Boolean)})}/>
            <textarea className='ui-textarea ui-textarea--md' placeholder='Ограничения' value={(goalData.constraints||[]).join('\n')} onChange={e=>updateGoal({constraints:e.target.value.split('\n').filter(Boolean)})}/>
            <textarea className='ui-textarea ui-textarea--md' placeholder='Предпосылки и допущения' value={(goalData.assumptions||[]).join('\n')} onChange={e=>updateGoal({assumptions:e.target.value.split('\n').filter(Boolean)})}/>
          </div>
          <div className='ui-card'><h4>Метрики успеха</h4><Button variant='secondary' onClick={addMetric}>Добавить метрику</Button>{(goalData.successMetrics||[]).map((m:any,i:number)=><div key={i} className='metric-row'><input className='ui-input' placeholder='Метрика' value={m.metric||''} onChange={e=>{const arr=[...(goalData.successMetrics||[])]; arr[i]={...m,metric:e.target.value}; updateGoal({successMetrics:arr})}}/><input className='ui-input' placeholder='Текущее значение' value={m.currentValue||''} onChange={e=>{const arr=[...(goalData.successMetrics||[])]; arr[i]={...m,currentValue:e.target.value}; updateGoal({successMetrics:arr})}}/><input className='ui-input' placeholder='Целевое значение' value={m.targetValue||''} onChange={e=>{const arr=[...(goalData.successMetrics||[])]; arr[i]={...m,targetValue:e.target.value}; updateGoal({successMetrics:arr})}}/><input className='ui-input' placeholder='Как измеряем' value={m.measurement||''} onChange={e=>{const arr=[...(goalData.successMetrics||[])]; arr[i]={...m,measurement:e.target.value}; updateGoal({successMetrics:arr})}}/><input className='ui-input' placeholder='Источник данных' value={m.dataSource||''} onChange={e=>{const arr=[...(goalData.successMetrics||[])]; arr[i]={...m,dataSource:e.target.value}; updateGoal({successMetrics:arr})}}/></div>)}</div>
          <div className='ui-card'><h4>SMART-анализ</h4>{Object.entries(goalData.smartAnalysis||{}).map(([k,v]:any)=><div key={k} className='smart-row'><div className='sub'><b>{k}</b>: {v.comment}</div><Button variant='secondary'>Исправить с AI</Button></div>)}</div>
          <div className='ui-card'><h4>AI Drafts</h4>{goalDraft ? (goalDraft.goal_options||[]).map((o:any,i:number)=><div key={i} className='ui-card'><b>{o.title||`Вариант ${i+1}`}</b><div className='sub'>{o.description}</div><div className='ui-actions'><Button variant='primary' onClick={()=>applyGoalOption(o,'select')}>Выбрать</Button><Button variant='secondary' onClick={()=>applyGoalOption(o,'merge')}>Объединить</Button><Button variant='secondary'>Редактировать</Button></div></div>) : <div className='sub'>Сначала запустите генерацию целей.</div>}</div>
          <div className='ui-card'><h4>Impact Map</h4><div className='impact-col'><span>Цель → Проблемы → KPI → Бизнес-эффект → Требования → Use Cases → Финальный БТ</span></div></div>
          <div className='ui-card'><h4>AI Questions</h4>{(goalData.aiQuestions||[]).map((q:string,i:number)=><div key={i} className='sub'>• {q}</div>)}<input className='ui-input' placeholder='Ответьте на вопрос AI...' value={goalQuestion} onChange={e=>setGoalQuestion(e.target.value)}/><Button variant='secondary' onClick={askGoal}>Отправить AI</Button>{goalPatch && <div className='ui-card'><div className='sub'>AI предлагает patch</div><div className='ui-actions'><Button variant='primary' onClick={applyGoalPatch}>Применить</Button><Button variant='secondary' onClick={()=>setGoalPatch(null)}>Отклонить</Button></div></div>}</div>
        </div> : <div className='artifact-draft'><h4 className='subhead'>Черновик артефакта</h4><p className='sub'>Заполните раздел вручную или используйте генерацию mock-агентом.</p><RichEditor value={content} onChange={(html,json)=>{setContent(html); setRichJson(json)}} /></div>}</ErrorBoundary>
        
        {active==='FINAL_BT' && <div className='ui-card page-section-gap'><h4>Preview финального БТ</h4><div className='sub'>Sections, зависящие от Goal: BUSINESS_EFFECT, AS_IS, TO_BE, USE_CASES, REQUIREMENTS, RISKS, FINAL_BT.</div></div>}<div className='sub'>Autosave: {saving==='saving'?'Сохранение…':saving==='saved'?'Сохранено':saving==='error'?'Ошибка сохранения':'—'}</div>
        {msg && <p className={`sub ${msg==='Сохранено' || msg==='Генерация завершена' ? '' : ''}`}>{msg}</p>}
      </div>
    </section>
    <AIAssistantPanel
      activeStage={active}
      stageLabel={current?.label || active}
      messages={assistantMessages}
      input={assistantInput}
      loading={assistantLoading}
      applying={assistantApplying}
      error={assistantError}
      pendingAction={assistantPendingAction}
      onInputChange={setAssistantInput}
      onSend={sendAssistantMessage}
      onSuggestedAction={handleAssistantSuggestedAction}
    />
  </div>
}
