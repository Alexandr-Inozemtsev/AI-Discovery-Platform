import { CheckCircle2, Circle, Download, MoreHorizontal, Database, RefreshCcw } from 'lucide-react'
import RichEditor from '../components/RichEditor'
import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams, useSearchParams } from 'react-router-dom'
import { api } from '../api/client'
import { ArtifactType, Project } from '../types/discovery'



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

export default function ProjectPage(){
  const {projectId}=useParams(); const navigate = useNavigate(); const [searchParams] = useSearchParams(); const [project,setProject]=useState<Project|null>(null); const [active,setActive]=useState<ArtifactType>('CONTEXT')
  const [content,setContent]=useState(''); const [richJson,setRichJson]=useState<any>(null); const [structured,setStructured]=useState<any>({}); const [ver,setVer]=useState<number|null>(null); const [updated,setUpdated]=useState('');
  const [cmp,setCmp]=useState<any>(null); const [msg,setMsg]=useState(''); const [busy,setBusy]=useState(false); const [saving,setSaving]=useState<'idle'|'saving'|'saved'|'error'>('idle');
  const [contextInput,setContextInput]=useState<ContextInput>(emptyInput); const [documents,setDocuments]=useState<any[]>([]); const [links,setLinks]=useState<string[]>([]); const [knowledge,setKnowledge]=useState<any>(null); const [thinking,setThinking]=useState(false); const [contextReady,setContextReady]=useState(false); const [problemDraft,setProblemDraft]=useState<any>({main_problem:'',user_pains:[],business_pains:[],root_causes:[],consequences_if_not_solved:[],evidence_signals:[],problem_statement:'',assumptions:[],missing_information:[],clarifying_questions:[],ai_chat_history:[],versions:[],status:'draft',source_context_version:0}); const [problemPatch,setProblemPatch]=useState<any>(null); const [problemChat,setProblemChat]=useState('')
  const current=tabs.find(t=>t.type===active)

  const loadCompletion=async()=>setCmp(await api<any>(`/projects/${projectId}/completion`).catch(()=>null))
  const load=async()=>{try{setProject(await api<Project>(`/projects/${projectId}`)); await loadCompletion()}catch{setMsg('Проект не найден')}}
  const loadArtifact=async(type:ArtifactType)=>{try{const a=await api<any>(`/projects/${projectId}/artifacts/${type}`);setContent(a.rendered_html||a.content||'');setRichJson(a.rich_content_json||null);setStructured(a.structured_content||{});setVer(a.version);setUpdated(a.updated_at); if(type==='CONTEXT'){const sc=a.structured_content||{}; setContextInput(sc?.context_input||emptyInput); setDocuments(sc?.uploaded_files||sc?.documents||[]); setLinks(sc?.links||[]); setKnowledge(sc?.extracted_knowledge||null); setContextReady(true)} if(type==='PROBLEM'){setProblemDraft({...problemDraft,...(a.structured_content||{})})}}catch{setContent('');setRichJson(null);setStructured({});setVer(null);setUpdated(''); if(type==='CONTEXT'){setContextInput(emptyInput); setDocuments([]); setLinks([]); setKnowledge(null); setContextReady(true); try{await api<any>(`/projects/${projectId}/artifacts/CONTEXT`,{method:'PUT',body:JSON.stringify({content:'',structured_content:{context_input:emptyInput,links:[],uploaded_files:[],extracted_knowledge:null,knowledge_coverage:{},indexing_status:'idle'}})})}catch{}}}}
  useEffect(()=>{load(); if(projectId) localStorage.setItem('lastOpenedProjectId', projectId)},[projectId]);
  useEffect(()=>{const st = searchParams.get('stage') as ArtifactType | null; if(st && tabs.some(t=>t.type===st)) setActive(st)},[searchParams]);
  useEffect(()=>{loadArtifact(active); if(projectId) navigate(`/projects/${projectId}?stage=${active}`, { replace:true })},[active,projectId])

  const save=async()=>{try{setSaving('saving');const payload=active==='GOAL'?{content:smartToText(structured),structured_content:structured,rich_content_json:richJson,rendered_html:content}:active==='CONTEXT'?{content:'',structured_content:buildContextPayload(),rich_content_json:null,rendered_html:null}:{content,structured_content:null,rich_content_json:richJson,rendered_html:content}; const a=await api<any>(`/projects/${projectId}/artifacts/${active}`,{method:'PUT',body:JSON.stringify(payload)});setVer(a.version);setUpdated(a.updated_at);setMsg('Сохранено');setSaving('saved');await loadCompletion()}catch{setMsg('Ошибка сохранения');setSaving('error')}}
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

  const smartToText=(s:any)=>`Цель проекта (SMART):\n${s.goal_text||''}\n\nS: ${s.specific||''}\nM: ${s.measurable||''}\nA: ${s.achievable||''}\nR: ${s.relevant||''}\nT: ${s.time_bound||''}`
  const bind=(k:string,ph:string)=><input className='input' placeholder={ph} value={structured[k]||''} onChange={e=>setStructured({...structured,[k]:e.target.value})}/>

  if(!project) return <div className='card'>Проект не найден</div>
  return <div className='workspace-grid'>
    <aside className='card'>
      <div className='sub'>Текущий проект</div>
      <div className='project-pick'>{project.project_name}</div>
      <h4>Этапы Discovery</h4>
      <div className='sub'>Общий прогресс: <b>{cmp?.completion_percent ?? 0}%</b></div>
      <div className='progress'><div style={{width:`${cmp?.completion_percent ?? 0}%`}}/></div>
      {tabs.map(t=>{const s=cmp?.sections?.find((x:any)=>x.artifact_type===t.type)?.status||'not_started'; return <div key={t.type} className={`sidebar-item ${active===t.type?'active':''}`} onClick={()=>setActive(t.type)}>{s==='completed'?<CheckCircle2 size={15} color='#22c55e'/>:s==='in_progress'?<Circle size={15} color='#2563eb'/>:<Circle size={15} color='#9ca3af'/>}<span>{t.label}</span></div>})}
    </aside>

    <section>
      <div className='card' style={{marginBottom:12}}>
        <div className='timeline'>{tabs.map(t=>{const s=cmp?.sections?.find((x:any)=>x.artifact_type===t.type)?.status||'not_started'; return <span key={t.type} className={`chip ${s}`}>{t.label}</span>})}</div>
      </div>

      <div className='card'>
        <div style={{display:'flex',justifyContent:'space-between',alignItems:'start',gap:8}}>
          <div><button className='btn' onClick={async()=>{if(active==='CONTEXT'){await saveContextInput(); if(saving==='error'){setMsg('Ошибка сохранения. Данные не отправлены'); return}} else {await save()} navigate('/')}}>← К списку проектов</button><h2 style={{margin:'10px 0 4px'}}>{current?.label}</h2><p className='sub' style={{margin:0}}>{project.project_name} · В работе · Версия {ver??0} · Обновлено: {updated?new Date(updated).toLocaleString('ru-RU'):'—'}</p></div>
          <div style={{display:'flex',alignItems:'center',gap:8,flexWrap:'wrap'}}><span className='sub'>Версия: {ver??0}</span><span className='sub'>Обновлено: {updated?new Date(updated).toLocaleString('ru-RU'):'—'}</span><button className='btn primary' onClick={save}>Сохранить</button><button className='btn' onClick={gen} disabled={busy}>Сгенерировать</button><button className='btn' onClick={validate} disabled={busy}>Проверить</button><a className='btn' href={`http://localhost:8000/api/projects/${projectId}/export/docx`}><Download size={16}/></a><button className='btn'><MoreHorizontal size={16}/></button></div>
        </div>

        {active==='CONTEXT' ? <div className='context-workspace'>
          <div className='context-left card'>
            <h4>Обзор</h4>
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
            <div style={{display:'flex',justifyContent:'space-between',alignItems:'center'}}><h4>Источники знаний</h4><button className='btn primary' onClick={runContextAnalyze} disabled={thinking}>{thinking?'Индексация...':'Запустить индексацию'}</button></div>
            <div className='card'><b>Документы</b><div className='sub'>Drag & Drop (метаданные на этом этапе)</div><input type='file' multiple onChange={e=>{const files=Array.from(e.target.files||[]).map((f:any)=>({name:f.name,type:f.type||'unknown',size:f.size,created_at:new Date().toISOString(),ai_status:'в очереди'})); setDocuments([...(documents||[]),...files])}}/></div>
            <div className='ai-sections'>{Array.isArray(documents) ? documents.map((d:any,i:number)=><div key={i} className='card'><div><b>Название:</b> {safeText(d?.name)}</div><div><b>Тип:</b> {safeText(d?.type || '—')}</div><div><b>Размер:</b> {formatFileSize(d?.size)}</div><div><b>Статус AI:</b> {safeText(d?.ai_status || 'в очереди')}</div><div><b>Дата загрузки:</b> {safeText(d?.created_at ? new Date(d.created_at).toLocaleString('ru-RU') : '—')}</div></div>) : []}</div>
            <div className='card'><b>Ссылки</b><input className='input' placeholder='Добавить ссылку' onKeyDown={e=>{if(e.key==='Enter'){e.preventDefault(); const v=(e.target as HTMLInputElement).value.trim(); if(v){setLinks([...(links||[]),JSON.stringify({url:v,type:detectLinkType(v),status:'Добавлено, ожидает обработки',created_at:new Date().toISOString()})]); (e.target as HTMLInputElement).value=''}}}}/><div className='ai-sections'>{Array.isArray(links) ? links.map((l:any,i)=>{let item:any=l; try{item=typeof l==='string' && l.startsWith('{')?JSON.parse(l):l}catch{} return <div key={i} className='card'><div><b>{safeText(item?.type||detectLinkType(safeText(l)))}</b></div><div className='sub'>{safeText(item?.url||l)}</div><div className='sub'>{safeText(item?.status||'Добавлено, ожидает обработки')} · {safeText(item?.created_at?new Date(item.created_at).toLocaleString('ru-RU'):'')}</div></div>}) : []}</div></div>
          </div>
          <div className='context-right card'>
            <h4><Database size={16}/> Извлечённые знания (AI)</h4><div style={{display:'flex',gap:8,marginBottom:8}}><button className='btn' onClick={runContextAnalyze}>Обновить извлечение</button><button className='btn' onClick={()=>setMsg('Показаны все извлечённые знания')}>Показать все извлечённые знания</button><button className='btn' onClick={()=>setMsg('Скопировано в следующий этап')}>Скопировать в следующий этап</button></div>
            {knowledge ? <div className='ai-sections'>{['процессы','системы','роли','интеграции','kpi','бизнес_сущности','документы','термины'].map((k)=><div className='card' key={k}><b>{k}</b><div className='timeline'>{Array.isArray(knowledge[k]) ? knowledge[k].map((x:any,i:number)=><span key={i} className='chip in_progress'>{safeText(x)}</span>) : []}</div></div>)}<div className='card'><b>Покрытие знаний</b><ul>{Object.entries(knowledge?.покрытие||knowledge?.coverage||{}).map(([k,v]:any)=><li key={k}>{safeText(v)} — {k}</li>)}</ul><div className='sub'>Что ещё можно добавить: BPMN, KPI, SLA, ограничения, Jira/Confluence/Figma ссылки.</div></div></div> : <p className='sub'>После индексации здесь появятся извлечённые знания.</p>}
            <button className='btn' onClick={runContextAnalyze}><RefreshCcw size={14}/> Переиндексировать</button>
          </div>
        </div> : active==='PROBLEM' ? <div className='problem-workspace'>
          <div className='problem-left card'><h4>Контекст для анализа</h4><div className='sub'>{contextInput.initiative_name}</div><div className='sub'>{contextInput.short_description}</div><div className='sub'>Процессы: {safeText((knowledge?.процессы||knowledge?.processes||[]).slice(0,5))}</div><div className='sub'>Системы: {safeText((knowledge?.системы||knowledge?.systems||[]).slice(0,5))}</div><div className='sub'>Роли: {safeText((knowledge?.роли||knowledge?.roles||[]).slice(0,5))}</div><button className='btn' onClick={()=>loadArtifact('CONTEXT')}>Обновить из контекста</button>{problemDraft.source_context_version && ver && problemDraft.source_context_version<ver ? <div className='card'><p className='sub'>Контекст изменился. Рекомендуется обновить анализ проблемы.</p><button className='btn' onClick={generateProblem}>Обновить проблему по новому контексту</button></div>:null}</div>
          <div className='problem-center card'><h4>Формулировка проблемы</h4><textarea className='textarea' placeholder='В чём проблема?' value={problemDraft.main_problem||''} onChange={e=>setProblemDraft({...problemDraft,main_problem:e.target.value})}/><label className='sub'>Problem Statement</label><textarea className='textarea' value={problemDraft.problem_statement||''} onChange={e=>setProblemDraft({...problemDraft,problem_statement:e.target.value})}/><div style={{display:'flex',gap:8,flexWrap:'wrap'}}><button className='btn primary' onClick={generateProblem} disabled={thinking}>{thinking?'Генерация...':'Сгенерировать'}</button><button className='btn' onClick={generateProblem}>Перегенерировать</button><button className='btn' onClick={()=>saveProblem()}>Сохранить</button><button className='btn' onClick={()=>saveProblem('ready')}>Принять как финальную проблему</button><button className='btn' onClick={()=>{const v=(problemDraft.versions||[]).slice(-1)[0]?.snapshot; if(v) setProblemDraft({...problemDraft,...v})}}>Вернуть предыдущую версию</button></div><div className='sub'>Статус: {safeText(problemDraft.status||'draft')}</div></div>
          <div className='problem-right card'><h4>AI уточняющие вопросы</h4><div className='ai-sections'>{(problemDraft.ai_chat_history||[]).map((m:any,i:number)=><div key={i} className='card'><b>{m.role==='user'?'Вы':'AI'}</b><div className='sub'>{safeText(m.text)}</div></div>)}</div><input className='input' placeholder='Ответьте AI...' value={problemChat} onChange={e=>setProblemChat(e.target.value)}/><button className='btn' onClick={askProblem}>Отправить</button>{problemPatch && <div className='card'><div className='sub'>AI предлагает изменения.</div><div style={{display:'flex',gap:8}}><button className='btn primary' onClick={applyPatch}>Применить</button><button className='btn' onClick={()=>setProblemPatch(null)}>Отклонить</button><button className='btn' onClick={()=>setMsg('Частичное применение доступно в следующем релизе')}>Применить частично</button></div></div>}</div>
        </div> : active==='GOAL' ? <div className='goal-layout'>
          <div>
            <label className='sub'>Цель проекта (SMART)</label>
            <textarea className='textarea' value={structured.goal_text||''} onChange={e=>setStructured({...structured,goal_text:e.target.value})}/>
            <div className='goal-grid'>
              {bind('specific','S — Specific / Конкретность')}
              {bind('measurable','M — Measurable / Измеримость')}
              {bind('achievable','A — Achievable / Достижимость')}
              {bind('relevant','R — Relevant / Значимость')}
              {bind('time_bound','T — Time-bound / Срок')}
            </div>
          </div>
          <div>
            <div className='card' style={{marginBottom:10}}><h4 style={{marginTop:0}}>Что нужно сделать?</h4><p className='sub'>Заполните SMART-структуру: цель должна быть конкретной, измеримой, достижимой, значимой и ограниченной по сроку.</p></div>
            <div className='card'><h4 style={{marginTop:0}}>Подсказка</h4><p className='sub'>Используйте количественные KPI, чтобы этап автоматически перешёл в «заполнено».</p></div>
          </div>
        </div> : <div style={{marginTop:14}}><h4 style={{margin:'0 0 6px'}}>Черновик артефакта</h4><p className='sub'>Заполните раздел вручную или используйте генерацию mock-агентом.</p><RichEditor value={content} onChange={(html,json)=>{setContent(html); setRichJson(json)}} /></div>}
        {active==='CONTEXT' && <div className='card' style={{marginTop:12}}><b>Контекст изменён. Это может повлиять на разделы:</b><ul><li>Проблема</li><li>Цель</li><li>AS IS</li><li>TO BE</li><li>Требования</li><li>Риски</li><li>Финальный БТ</li></ul><div style={{display:'flex',gap:8}}><button className='btn' onClick={()=>setMsg('Помечено: требует обновления')}>Обновить зависимые разделы</button><button className='btn' onClick={()=>setMsg('Изменения контекста доступны для просмотра')}>Посмотреть изменения</button><button className='btn' onClick={()=>setMsg('Оставлено как есть')}>Оставить как есть</button></div></div>}
        <div className='card' style={{marginTop:12}}><h4 style={{marginTop:0}}>Как работает Discovery в платформе</h4><div className='flow-grid'>{workflowStages.map(([key,text],idx)=><div key={key} className={`flow-step ${active===key?'active':''}`}><b>{idx+1}. {tabs.find(t=>t.type===key)?.label}</b><p className='sub'>{text}</p></div>)}</div><p className='sub'>AI постоянно использует контекст на всех этапах и обновляет артефакты при изменениях.</p></div>
        <div className='card' style={{marginTop:12}}><h4 style={{marginTop:0}}>Как AI помогает на каждом этапе</h4><p className='sub'>Источники: документы, ссылки, ручное описание.</p><p className='sub'>AI делает: извлекает процессы, системы, роли, интеграции, термины.</p><p className='sub'>Человек делает: проверяет, дополняет, подтверждает корректность.</p><button className='btn primary' onClick={()=>setActive('PROBLEM')}>Перейти к следующему этапу</button></div>
        <div className='sub'>Autosave: {saving==='saving'?'Сохранение…':saving==='saved'?'Сохранено':saving==='error'?'Ошибка сохранения':'—'}</div>
        {msg && <p className={`sub ${msg==='Сохранено' || msg==='Генерация завершена' ? '' : ''}`}>{msg}</p>}
      </div>
    </section>
  </div>
}
