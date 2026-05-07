import { Download, MoreHorizontal, Database, RefreshCcw, FileText, FileSpreadsheet, File, Link2, Figma } from 'lucide-react'
import RichEditor from '../components/RichEditor'
import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams, useSearchParams } from 'react-router-dom'
import { api } from '../api/client'
import { ArtifactType, Project } from '../types/discovery'
import AIActionBar from '../ui/components/AIActionBar'





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
}
const emptyInput:ContextInput={initiative_name:'',short_description:'',initiative_goal:'',business_domain:'',process_owner:'',discovery_owner:'',related_processes:'',related_systems:''}


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
  const [cmp,setCmp]=useState<any>(null); const [pipeline,setPipeline]=useState<Record<string,any>>({}); const [msg,setMsg]=useState(''); const [aiActionLoading,setAiActionLoading]=useState<string|null>(null); const [goalDraft,setGoalDraft]=useState<any>(null); const [busy,setBusy]=useState(false); const [saving,setSaving]=useState<'idle'|'saving'|'saved'|'error'>('idle');
  const [contextInput,setContextInput]=useState<ContextInput>(emptyInput); const [linkDraft,setLinkDraft]=useState(''); const [goalQuestion,setGoalQuestion]=useState(''); const [goalPatch,setGoalPatch]=useState<any>(null); const [documents,setDocuments]=useState<any[]>([]); const [links,setLinks]=useState<string[]>([]); const [knowledge,setKnowledge]=useState<any>(null); const [thinking,setThinking]=useState(false); const [contextReady,setContextReady]=useState(false); const [problemDraft,setProblemDraft]=useState<any>({main_problem:'',user_pains:[],business_pains:[],root_causes:[],consequences_if_not_solved:[],evidence_signals:[],problem_statement:'',assumptions:[],missing_information:[],clarifying_questions:[],ai_chat_history:[],versions:[],status:'draft',source_context_version:0}); const [problemPatch,setProblemPatch]=useState<any>(null); const [problemChat,setProblemChat]=useState('')
  const current=tabs.find(t=>t.type===active)

  const loadCompletion=async()=>{setCmp(await api<any>(`/projects/${projectId}/completion`).catch(()=>null)); const arts=await api<any[]>(`/projects/${projectId}/artifacts`).catch(()=>[]); const p:Record<string,any>={}; arts.forEach(a=>p[a.artifact_type]=a.structured_content?.pipeline_meta||{status:(a.content||'').trim()?'ready':'empty',version:a.version,updated_at:a.updated_at,source_artifacts:[],source_versions:{}}); setPipeline(p)}
  const load=async()=>{try{setProject(await api<Project>(`/projects/${projectId}`)); await loadCompletion()}catch{setMsg('Проект не найден')}}
  const loadArtifact=async(type:ArtifactType)=>{try{const a=await api<any>(`/projects/${projectId}/artifacts/${type}`);setContent(a.rendered_html||a.content||'');setRichJson(a.rich_content_json||null);setStructured(a.structured_content||{});setVer(a.version);setUpdated(a.updated_at); if(type==='CONTEXT'){const sc=a.structured_content||{}; setContextInput(sc?.context_input||emptyInput); setDocuments(sc?.uploaded_files||sc?.documents||[]); setLinks(sc?.links||[]); setKnowledge(sc?.extracted_knowledge||null); setContextReady(true)} if(type==='PROBLEM'){setProblemDraft({...problemDraft,...(a.structured_content||{})})} if(type==='GOAL'){setGoalDraft((a.structured_content||{}).aiDrafts||null)}}catch{setContent('');setRichJson(null);setStructured({});setVer(null);setUpdated(''); if(type==='CONTEXT'){setContextInput(emptyInput); setDocuments([]); setLinks([]); setKnowledge(null); setContextReady(true); try{await api<any>(`/projects/${projectId}/artifacts/CONTEXT`,{method:'PUT',body:JSON.stringify({content:'',structured_content:{context_input:emptyInput,links:[],uploaded_files:[],extracted_knowledge:null,knowledge_coverage:{},indexing_status:'idle'}})})}catch{}}}}
  useEffect(()=>{load(); if(projectId) localStorage.setItem('lastOpenedProjectId', projectId)},[projectId]);
  useEffect(()=>{const st = searchParams.get('stage') as ArtifactType | null; if(st && tabs.some(t=>t.type===st)) setActive(st)},[searchParams]);
  useEffect(()=>{loadArtifact(active); if(projectId) navigate(`/projects/${projectId}?stage=${active}`, { replace:true })},[active,projectId])


  const markDependentsStale=async(changed:ArtifactType, changedVersion:number)=>{try{const idx=stageOrder.indexOf(changed); if(idx<0) return; const dependents=stageOrder.slice(idx+1); for(const dep of dependents){const art=await api<any>(`/projects/${projectId}/artifacts/${dep}`).catch(()=>null); if(!art) continue; const sc=art.structured_content||{}; const meta=sc.pipeline_meta||{status:'draft',source_artifacts:[],source_versions:{},generated_at:null}; const nextMeta={...meta,status:'stale',source_artifacts:[...(meta.source_artifacts||[]),changed].filter((v:any,i:number,a:any[])=>a.indexOf(v)===i),source_versions:{...(meta.source_versions||{}),[changed]:changedVersion},updated_at:new Date().toISOString()}; await api<any>(`/projects/${projectId}/artifacts/${dep}`,{method:'PUT',body:JSON.stringify({content:art.content||'',structured_content:{...sc,pipeline_meta:nextMeta},rich_content_json:art.rich_content_json||null,rendered_html:art.rendered_html||null})})}
  }catch{}}

  const save=async()=>{try{setSaving('saving');const baseMeta={stage:active,status:'manually_edited',source_artifacts:stageOrder.slice(0,Math.max(0,stageOrder.indexOf(active))),source_versions:{},version:ver||0,updated_at:new Date().toISOString(),generated_at:null}; const payload=active==='GOAL'?{content:smartToText(goalData),structured_content:{...goalData,pipeline_meta:baseMeta},rich_content_json:richJson,rendered_html:content}:active==='CONTEXT'?{content:'',structured_content:{...buildContextPayload(),pipeline_meta:baseMeta},rich_content_json:null,rendered_html:null}:{content,structured_content:{pipeline_meta:baseMeta},rich_content_json:richJson,rendered_html:content}; const a=await api<any>(`/projects/${projectId}/artifacts/${active}`,{method:'PUT',body:JSON.stringify(payload)});setVer(a.version);setUpdated(a.updated_at);setMsg('Сохранено');setSaving('saved'); await markDependentsStale(active,a.version); await loadCompletion()}catch{setMsg('Ошибка сохранения');setSaving('error')}}
  const gen=async()=>{try{setBusy(true);const a=await api<any>(`/projects/${projectId}/generate/${active}`,{method:'POST'});setContent(a.content);setStructured({});setVer(a.version);setUpdated(a.updated_at);setMsg('Генерация завершена');await loadCompletion()}catch{setMsg('Ошибка сохранения')}finally{setBusy(false)}}
  const validate=async()=>{try{setBusy(true);await api<any>(`/projects/${projectId}/validate`,{method:'POST'});setMsg('Сохранено');await loadCompletion()}catch{setMsg('Ошибка сохранения')}finally{setBusy(false)}}
  useEffect(()=>{if(active==='GOAL' || active==='CONTEXT' || active==='PROBLEM') return; if(!content) return; const t=setTimeout(()=>{save()},2000); return ()=>clearTimeout(t)},[content])
  useEffect(()=>{if(active!=='PROBLEM') return; const t=setTimeout(()=>{saveProblem()},900); return ()=>clearTimeout(t)},[problemDraft])
  useEffect(()=>{if(active!=='CONTEXT' || !contextReady) return; const t=setTimeout(()=>{saveContextInput()},800); return ()=>clearTimeout(t)},[contextInput,documents,links,knowledge,contextReady])


  const buildContextPayload=()=>({
    initiative_name: contextInput.initiative_name,
    short_description: contextInput.short_description,
    initiative_goal: contextInput.initiative_goal,
    business_domain: contextInput.business_domain,
    process_owner: contextInput.process_owner,
    discovery_owner: contextInput.discovery_owner,
    related_processes: contextInput.related_processes,
    related_systems: contextInput.related_systems,
    context_input: contextInput,
    links,
    uploaded_files: documents,
    extracted_knowledge: knowledge,
    knowledge_coverage: knowledge?.покрытие || {},
    indexing_status: structured?.indexing_status || 'idle',
    indexed_at: structured?.indexed_at || null,
    knowledge_history: structured?.knowledge_history||[]
  })

  const saveContextInput=async()=>{try{if(!projectId) return; setSaving('saving'); const a=await api<any>(`/projects/${projectId}/artifacts/CONTEXT`,{method:'PUT',body:JSON.stringify({content:'',structured_content:buildContextPayload()})}); setVer(a.version); setUpdated(a.updated_at); setStructured(a.structured_content||{}); setSaving('saved')}catch{setSaving('error'); setMsg('Ошибка сохранения контекста')}}
  const runContextAnalyze=async()=>{try{setThinking(true); const r=await api<any>(`/projects/${projectId}/context/analyze`,{method:'POST',body:JSON.stringify({context_input:contextInput,documents,links})}); const now=new Date().toISOString(); const nextDocs=(Array.isArray(documents)?documents:[]).map((d:any)=>({...d,ai_status:'проиндексирован'})); setDocuments(nextDocs); setKnowledge(r.extracted_knowledge); setStructured({...structured,indexing_status:r.indexing_status||'completed',indexed_at:now}); setMsg('Индексация знаний завершена'); await saveContextInput()}catch{setMsg('Ошибка индексации')}finally{setThinking(false)}}


  const generateProblem=async()=>{try{setThinking(true); const r=await api<any>(`/projects/${projectId}/problem/generate`,{method:'POST'}); setProblemDraft(r.structured_content||problemDraft); setMsg('Черновик проблемы сгенерирован')}catch{setMsg('Ошибка генерации проблемы')}finally{setThinking(false)}}
  const saveProblem=async(status?:string)=>{try{setSaving('saving'); const next={...problemDraft,status:status||problemDraft.status}; const a=await api<any>(`/projects/${projectId}/artifacts/PROBLEM`,{method:'PUT',body:JSON.stringify({content:next.problem_statement||next.main_problem||'',structured_content:next})}); setProblemDraft(a.structured_content||next); setSaving('saved'); setMsg('Проблема сохранена')}catch{setSaving('error'); setMsg('Ошибка сохранения проблемы')}}
  const askProblem=async()=>{try{setThinking(true); const r=await api<any>(`/projects/${projectId}/problem/ask`,{method:'POST',body:JSON.stringify({message:problemChat,draft:problemDraft})}); setProblemPatch(r.patch); setProblemDraft({...problemDraft, ai_chat_history:[...(problemDraft.ai_chat_history||[]),{role:'user',text:problemChat},{role:'assistant',text:r.assistant_message}]}); setProblemChat('')}catch{setMsg('Ошибка AI уточнения')}finally{setThinking(false)}}
  const applyPatch=async()=>{if(!problemPatch) return; try{const r=await api<any>(`/projects/${projectId}/problem/apply-patch`,{method:'POST',body:JSON.stringify({patch:{...problemDraft,...problemPatch},status:'needs_clarification'})}); setProblemDraft(r.structured_content||problemDraft); setProblemPatch(null); setMsg('Изменения применены')}catch{setMsg('Ошибка применения изменений')}}

  const smartToText=(goal:GoalDraft)=>`Цель инициативы: ${goal.title}\nПроблема: ${goal.businessProblem}\nЖелаемый результат: ${goal.desiredOutcome}\nKPI: ${(goal.successMetrics||[]).map(m=>`${m.metric}: ${m.currentValue||'—'} -> ${m.targetValue}`).join('; ')}`
  const toArray=(v:any)=>Array.isArray(v)?v:[]
  const updateGoal=(patch:Partial<GoalDraft>)=>setStructured({...goalData,...patch,updatedAt:new Date().toISOString()})
  const goalData:GoalDraft = { ...emptyGoal(), ...(structured||{}) }
  const addListItem=(key:'nonGoals'|'assumptions'|'risks'|'constraints'|'stakeholders',val:string)=>{ if(!val.trim()) return; updateGoal({[key]:[...toArray(goalData[key]),val.trim()] } as any) }
  const removeListItem=(key:'nonGoals'|'assumptions'|'risks'|'constraints'|'stakeholders',idx:number)=> updateGoal({[key]:toArray(goalData[key]).filter((_:any,i:number)=>i!==idx)} as any)


  const runAiAction=async(key:string,fn:()=>Promise<void>)=>{try{setAiActionLoading(key); setMsg(''); await fn()}catch(e:any){setMsg(e?.message||'Ошибка AI действия')}finally{setAiActionLoading(null)}}
  const aiActionsByStage:Record<string,{key:string;label:string;enabled:boolean;onClick?:()=>void}[]>={
    CONTEXT:[{key:'ctx_index',label:'Проиндексировать контекст',enabled:true,onClick:()=>runAiAction('ctx_index',runContextAnalyze)},{key:'ctx_extract',label:'Извлечь знания',enabled:true,onClick:()=>runAiAction('ctx_extract',runContextAnalyze)},{key:'ctx_cov',label:'Проверить покрытие знаний',enabled:true,onClick:()=>runAiAction('ctx_cov',async()=>{await runContextAnalyze()})}],
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

  if(!project) return <div className='card'>Проект не найден</div>
  return <div className='workspace-single'>
    <section>
      <div className='card' style={{marginBottom:12}}>
        <div className='top-progress'><div><span className='sub'>Общий прогресс: <b>{cmp?.completion_percent ?? 0}%</b></span><div className='progress'><div style={{width:`${cmp?.completion_percent ?? 0}%`}}/></div></div></div>
        <div className='stage-tabs'>{tabs.map(t=>{const st=(pipeline[t.type]?.status||'empty'); return <button key={t.type} className={`stage-pill ${active===t.type?'active':''}`} onClick={()=>setActive(t.type)}>{t.label}<span className={`pipe-dot ${st}`}/></button>})}</div><div className='sub'>Зависимости: {stageOrder.slice(0,Math.max(0,stageOrder.indexOf(active))).map(s=>humanStage[s]).join(' → ')||'Нет'} · Статус: {pipeline[active]?.status||'empty'}</div><AIActionBar actions={aiActionsByStage[active]||[]} loading={aiActionLoading}/>
      </div>

      <div className='card'>
        <div style={{display:'flex',justifyContent:'space-between',alignItems:'start',gap:8}}>
          <div><h2 style={{margin:'0 0 4px'}}>{current?.label}</h2><p className='sub' style={{margin:0}}>{project.project_name} · В работе · Версия {ver??0} · Обновлено: {updated?new Date(updated).toLocaleString('ru-RU'):'—'}</p></div>
          <div style={{display:'flex',alignItems:'center',gap:8,flexWrap:'wrap'}}><span className='sub'>Версия: {ver??0}</span><span className='sub'>Обновлено: {updated?new Date(updated).toLocaleString('ru-RU'):'—'}</span><button className='btn primary' onClick={save}>Сохранить</button><button className='btn' onClick={gen} disabled={busy}>Сгенерировать</button><button className='btn' onClick={validate} disabled={busy}>Проверить</button><a className='btn' href={`http://localhost:8000/api/projects/${projectId}/export/docx`}><Download size={16}/></a><button className='btn'><MoreHorizontal size={16}/></button></div>
        </div>

        {active==='CONTEXT' ? <div className='context-workspace refined'>
          <div className='context-left card'>
            <h4>Обзор проекта</h4>
            <input className='input' placeholder='Название инициативы' value={contextInput.initiative_name} onChange={e=>setContextInput({...contextInput,initiative_name:e.target.value})}/>
            <textarea className='textarea' placeholder='Краткое описание' value={contextInput.short_description} onChange={e=>setContextInput({...contextInput,short_description:e.target.value})}/>
            <input className='input' placeholder='Цель инициативы' value={contextInput.initiative_goal} onChange={e=>setContextInput({...contextInput,initiative_goal:e.target.value})}/>
            <input className='input' placeholder='Бизнес-направление' value={contextInput.business_domain} onChange={e=>setContextInput({...contextInput,business_domain:e.target.value})}/>
            <input className='input' placeholder='Владелец процесса' value={contextInput.process_owner} onChange={e=>setContextInput({...contextInput,process_owner:e.target.value})}/>
            <input className='input' placeholder='Владелец Discovery' value={contextInput.discovery_owner} onChange={e=>setContextInput({...contextInput,discovery_owner:e.target.value})}/>
            <input className='input' placeholder='Связанные процессы' value={contextInput.related_processes} onChange={e=>setContextInput({...contextInput,related_processes:e.target.value})}/>
            <input className='input' placeholder='Связанные системы' value={contextInput.related_systems} onChange={e=>setContextInput({...contextInput,related_systems:e.target.value})}/>
          </div>
          <div className='context-center card'>
            <div style={{display:'flex',justifyContent:'space-between',alignItems:'center'}}><h4>Источники знаний</h4></div>
            <div className='sources-card'>
              <div className='sources-head'><b>Документы ({(Array.isArray(documents)&&documents.length)?documents.length:3})</b><label className='btn'>Загрузить файлы<input type='file' multiple style={{display:'none'}} onChange={e=>{const files=Array.from(e.target.files||[]).map((f:any)=>({name:f.name,type:f.type||'unknown',size:f.size,created_at:new Date().toISOString(),ai_status:'Проиндексирован'})); setDocuments([...(documents||[]),...files])}}/></label></div>
              <div className='sources-list'>{(Array.isArray(documents)&&documents.length?documents:demoDocs).map((d:any,i:number)=><div key={i} className='source-row'><div className='source-main'><span className={`source-ico ${sourceIcon(safeText(d?.name||''))}`}>{sourceIcon(safeText(d?.name||''))==='xls'?<FileSpreadsheet size={14}/>:sourceIcon(safeText(d?.name||''))==='doc'?<FileText size={14}/>:<File size={14}/>}</span><div><div className='source-title'>{safeText(d?.name)}</div><div className='source-meta'>{d.size?d.size:formatFileSize(d?.size)} • Загружен {safeText(d?.date || (d?.created_at ? new Date(d.created_at).toLocaleDateString('ru-RU') : '06.05.2026'))}</div></div></div><span className='status-green'>Проиндексирован</span></div>)}</div>
            </div>
            <div className='sources-card'>
              <b>Ссылки ({(Array.isArray(links)&&links.length)?links.length:4})</b>
              <div className='sources-list'>{((Array.isArray(links)&&links.length)?links:demoLinks).map((l:any,i)=>{let item:any=l; try{item=typeof l==='string' && l.startsWith('{')?JSON.parse(l):l}catch{} const title=safeText(item?.url||l); const type=safeText(item?.type||detectLinkType(title)); return <div key={i} className='source-row'><div className='source-main'><span className={`source-ico ${sourceIcon(type)}`}>{sourceIcon(type)==='figma'?<Figma size={14}/>:<Link2 size={14}/>}</span><div className='source-title'>{title}</div></div><span className='sub source-type'>{type}</span></div>})}</div>
              <div className='sources-add'><input className='input' placeholder='Добавить ссылку...' value={linkDraft} onChange={e=>setLinkDraft(e.target.value)} onKeyDown={e=>{if(e.key==='Enter'){e.preventDefault(); const v=linkDraft.trim(); if(v){setLinks([...(links||[]),JSON.stringify({url:v,type:detectLinkType(v),status:'Добавлено, ожидает обработки',created_at:new Date().toISOString()})]); setLinkDraft('')}}}}/><button className='btn primary' onClick={()=>{const v=linkDraft.trim(); if(!v) return; setLinks([...(links||[]),JSON.stringify({url:v,type:detectLinkType(v),status:'Добавлено, ожидает обработки',created_at:new Date().toISOString()})]); setLinkDraft('')}}>Добавить</button></div>
            </div>
          </div>
          <div className='context-right card'>
            <h4><Database size={16}/> Извлечённые знания (AI)</h4><div style={{display:'flex',gap:8,marginBottom:8}}><button className='btn' onClick={runContextAnalyze}>Обновить извлечение</button><button className='btn' onClick={()=>setMsg('Показаны все извлечённые знания')}>Показать все извлечённые знания</button><button className='btn' onClick={()=>setMsg('Скопировано в следующий этап')}>Скопировать в следующий этап</button></div>
            {knowledge ? <div className='ai-sections'>{['процессы','системы','роли','интеграции','kpi','бизнес_сущности','документы','термины'].map((k)=><div className='card' key={k}><b>{k}</b><div className='timeline'>{Array.isArray(knowledge[k]) ? knowledge[k].map((x:any,i:number)=><span key={i} className='chip in_progress'>{safeText(x)}</span>) : []}</div></div>)}<div className='card'><b>Покрытие знаний</b><ul>{Object.entries(knowledge?.покрытие||knowledge?.coverage||{}).map(([k,v]:any)=><li key={k}>{safeText(v)} — {k}</li>)}</ul><div className='sub'>Что ещё можно добавить: BPMN, KPI, SLA, ограничения, Jira/Confluence/Figma ссылки.</div></div></div> : <p className='sub'>После индексации здесь появятся извлечённые знания.</p>}
            <button className='btn' onClick={runContextAnalyze}><RefreshCcw size={14}/> Переиндексировать</button>
          </div>
          <div className='context-coverage card'><h4>Покрытие знаний</h4><ul className='coverage-list'><li>✅ Документы</li><li>✅ Процессы</li><li>✅ Системы</li><li>✅ Роли</li><li>✅ Интеграции</li><li>⚠ KPI</li><li>❌ BPMN</li><li>❌ SLA</li><li>⚠ Ограничения</li></ul><div className='hint-card'><b>Что ещё можно добавить</b><ul><li>Добавьте BPMN текущего процесса</li><li>Уточните KPI и целевые метрики</li><li>Добавьте ограничения и допущения</li></ul></div></div>
          <div className='ai-assistant card'><h4>AI-ассистент</h4><div className='card'><b>Рекомендации</b><p className='sub'>Добавьте BPMN диаграмму AS IS для более точного анализа.</p></div><div className='card'><b>Следующий шаг</b><p className='sub'>Перейдите к разделу «Проблема» для анализа.</p><button className='btn'>Перейти к проблеме</button></div><div className='card'><b>История индексации</b><p className='sub'>Успешно: документы и ссылки проиндексированы.</p></div><div style={{marginTop:'auto'}}><input className='input' placeholder='Спросите что угодно...'/></div></div>
        </div> : active==='PROBLEM' ? <div className='problem-workspace'>
          <div className='problem-left card'><h4>Контекст для анализа</h4><div className='sub'>{contextInput.initiative_name}</div><div className='sub'>{contextInput.short_description}</div><div className='sub'>Процессы: {safeText((knowledge?.процессы||knowledge?.processes||[]).slice(0,5))}</div><div className='sub'>Системы: {safeText((knowledge?.системы||knowledge?.systems||[]).slice(0,5))}</div><div className='sub'>Роли: {safeText((knowledge?.роли||knowledge?.roles||[]).slice(0,5))}</div><button className='btn' onClick={()=>loadArtifact('CONTEXT')}>Обновить из контекста</button>{problemDraft.source_context_version && ver && problemDraft.source_context_version<ver ? <div className='card'><p className='sub'>Контекст изменился. Рекомендуется обновить анализ проблемы.</p><button className='btn' onClick={generateProblem}>Обновить проблему по новому контексту</button></div>:null}</div>
          <div className='problem-center card'><h4>Формулировка проблемы</h4><textarea className='textarea' placeholder='В чём проблема?' value={problemDraft.main_problem||''} onChange={e=>setProblemDraft({...problemDraft,main_problem:e.target.value})}/><label className='sub'>Problem Statement</label><textarea className='textarea' value={problemDraft.problem_statement||''} onChange={e=>setProblemDraft({...problemDraft,problem_statement:e.target.value})}/><div style={{display:'flex',gap:8,flexWrap:'wrap'}}><button className='btn primary' onClick={generateProblem} disabled={thinking}>{thinking?'Генерация...':'Сгенерировать'}</button><button className='btn' onClick={generateProblem}>Перегенерировать</button><button className='btn' onClick={()=>saveProblem()}>Сохранить</button><button className='btn' onClick={()=>saveProblem('ready')}>Принять как финальную проблему</button><button className='btn' onClick={()=>{const v=(problemDraft.versions||[]).slice(-1)[0]?.snapshot; if(v) setProblemDraft({...problemDraft,...v})}}>Вернуть предыдущую версию</button></div><div className='sub'>Статус: {safeText(problemDraft.status||'draft')}</div></div>
          <div className='problem-right card'><h4>AI уточняющие вопросы</h4><div className='ai-sections'>{(problemDraft.ai_chat_history||[]).map((m:any,i:number)=><div key={i} className='card'><b>{m.role==='user'?'Вы':'AI'}</b><div className='sub'>{safeText(m.text)}</div></div>)}</div><input className='input' placeholder='Ответьте AI...' value={problemChat} onChange={e=>setProblemChat(e.target.value)}/><button className='btn' onClick={askProblem}>Отправить</button>{problemPatch && <div className='card'><div className='sub'>AI предлагает изменения.</div><div style={{display:'flex',gap:8}}><button className='btn primary' onClick={applyPatch}>Применить</button><button className='btn' onClick={()=>setProblemPatch(null)}>Отклонить</button><button className='btn' onClick={()=>setMsg('Частичное применение доступно в следующем релизе')}>Применить частично</button></div></div>}</div>
        </div> : active==='GOAL' ? <div className='goal-screen'>
          <div className='card'><h4>Источники для генерации цели</h4><div className='sub'>Контекст: {(contextInput.initiative_name||contextInput.short_description)?'заполнен':'не заполнен'} · Проблема: {(problemDraft.main_problem||problemDraft.problem_statement)?'заполнена':'не заполнена'}</div><div className='timeline'><span className='chip in_progress'>Процессы: {((knowledge?.процессы||knowledge?.processes||[]) as any[]).length}</span><span className='chip in_progress'>Системы: {((knowledge?.системы||knowledge?.systems||[]) as any[]).length}</span><span className='chip in_progress'>Корневые причины: {((problemDraft.root_causes||[]) as any[]).length}</span></div></div>
          <div className='card'><h4>Целевая формулировка</h4>
            <input className='input' placeholder='Название цели' value={goalData.title||''} onChange={e=>updateGoal({title:e.target.value})}/>
            <textarea className='textarea' style={{minHeight:80}} placeholder='Какую проблему решаем' value={goalData.businessProblem||''} onChange={e=>updateGoal({businessProblem:e.target.value})}/>
            <textarea className='textarea' style={{minHeight:80}} placeholder='Какой результат хотим получить' value={goalData.desiredOutcome||''} onChange={e=>updateGoal({desiredOutcome:e.target.value})}/>
            <textarea className='textarea' style={{minHeight:70}} placeholder='Почему это важно бизнесу' value={goalData.businessImportance||''} onChange={e=>updateGoal({businessImportance:e.target.value})}/>
            <textarea className='textarea' style={{minHeight:70}} placeholder='Что произойдет, если ничего не делать' value={goalData.noActionImpact||''} onChange={e=>updateGoal({noActionImpact:e.target.value})}/>
            <textarea className='textarea' style={{minHeight:70}} placeholder='Что НЕ входит в scope' value={(goalData.nonGoals||[]).join('\n')} onChange={e=>updateGoal({nonGoals:e.target.value.split('\n').filter(Boolean)})}/>
            <textarea className='textarea' style={{minHeight:70}} placeholder='Ограничения' value={(goalData.constraints||[]).join('\n')} onChange={e=>updateGoal({constraints:e.target.value.split('\n').filter(Boolean)})}/>
            <textarea className='textarea' style={{minHeight:70}} placeholder='Предпосылки и допущения' value={(goalData.assumptions||[]).join('\n')} onChange={e=>updateGoal({assumptions:e.target.value.split('\n').filter(Boolean)})}/>
          </div>
          <div className='card'><h4>Метрики успеха</h4><button className='btn' onClick={addMetric}>Добавить метрику</button>{(goalData.successMetrics||[]).map((m:any,i:number)=><div key={i} className='metric-row'><input className='input' placeholder='Метрика' value={m.metric||''} onChange={e=>{const arr=[...(goalData.successMetrics||[])]; arr[i]={...m,metric:e.target.value}; updateGoal({successMetrics:arr})}}/><input className='input' placeholder='Текущее значение' value={m.currentValue||''} onChange={e=>{const arr=[...(goalData.successMetrics||[])]; arr[i]={...m,currentValue:e.target.value}; updateGoal({successMetrics:arr})}}/><input className='input' placeholder='Целевое значение' value={m.targetValue||''} onChange={e=>{const arr=[...(goalData.successMetrics||[])]; arr[i]={...m,targetValue:e.target.value}; updateGoal({successMetrics:arr})}}/><input className='input' placeholder='Как измеряем' value={m.measurement||''} onChange={e=>{const arr=[...(goalData.successMetrics||[])]; arr[i]={...m,measurement:e.target.value}; updateGoal({successMetrics:arr})}}/><input className='input' placeholder='Источник данных' value={m.dataSource||''} onChange={e=>{const arr=[...(goalData.successMetrics||[])]; arr[i]={...m,dataSource:e.target.value}; updateGoal({successMetrics:arr})}}/></div>)}</div>
          <div className='card'><h4>SMART-анализ</h4>{Object.entries(goalData.smartAnalysis||{}).map(([k,v]:any)=><div key={k} className='smart-row'><div className='sub'><b>{k}</b>: {v.comment}</div><button className='btn'>Исправить с AI</button></div>)}</div>
          <div className='card'><h4>AI Drafts</h4>{goalDraft ? (goalDraft.goal_options||[]).map((o:any,i:number)=><div key={i} className='card'><b>{o.title||`Вариант ${i+1}`}</b><div className='sub'>{o.description}</div><div style={{display:'flex',gap:8}}><button className='btn primary' onClick={()=>applyGoalOption(o,'select')}>Выбрать</button><button className='btn' onClick={()=>applyGoalOption(o,'merge')}>Объединить</button><button className='btn'>Редактировать</button></div></div>) : <div className='sub'>Сначала запустите генерацию целей.</div>}</div>
          <div className='card'><h4>Impact Map</h4><div className='impact-col'><span>Цель → Проблемы → KPI → Бизнес-эффект → Требования → Use Cases → Финальный БТ</span></div></div>
          <div className='card'><h4>AI Questions</h4>{(goalData.aiQuestions||[]).map((q:string,i:number)=><div key={i} className='sub'>• {q}</div>)}<input className='input' placeholder='Ответьте на вопрос AI...' value={goalQuestion} onChange={e=>setGoalQuestion(e.target.value)}/><button className='btn' onClick={askGoal}>Отправить AI</button>{goalPatch && <div className='card'><div className='sub'>AI предлагает patch</div><div style={{display:'flex',gap:8}}><button className='btn primary' onClick={applyGoalPatch}>Применить</button><button className='btn' onClick={()=>setGoalPatch(null)}>Отклонить</button></div></div>}</div>
        </div> : <div style={{marginTop:14}}><h4 style={{margin:'0 0 6px'}}>Черновик артефакта</h4><p className='sub'>Заполните раздел вручную или используйте генерацию mock-агентом.</p><RichEditor value={content} onChange={(html,json)=>{setContent(html); setRichJson(json)}} /></div>}
        {active!=='CONTEXT' && <div className='card' style={{marginTop:12}}><h4 style={{marginTop:0}}>Как работает Discovery в платформе</h4><div className='flow-grid'>{workflowStages.map(([key,text],idx)=><div key={key} className={`flow-step ${active===key?'active':''}`}><b>{idx+1}. {tabs.find(t=>t.type===key)?.label}</b><p className='sub'>{text}</p></div>)}</div><p className='sub'>AI постоянно использует контекст на всех этапах и обновляет артефакты при изменениях.</p></div>}
        <div className='sub'>Autosave: {saving==='saving'?'Сохранение…':saving==='saved'?'Сохранено':saving==='error'?'Ошибка сохранения':'—'}</div>
        {msg && <p className={`sub ${msg==='Сохранено' || msg==='Генерация завершена' ? '' : ''}`}>{msg}</p>}
      </div>
    </section>
  </div>
}
