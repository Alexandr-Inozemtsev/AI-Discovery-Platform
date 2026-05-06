import { CheckCircle2, Circle, Download, MoreHorizontal, Copy, RefreshCcw } from 'lucide-react'
import RichEditor from '../components/RichEditor'
import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams, useSearchParams } from 'react-router-dom'
import { api } from '../api/client'
import { ArtifactType, Project } from '../types/discovery'



type ContextInput = {
  initiative_name:string; idea_summary:string; business_context:string; pain_points:string; impacted_processes:string; impacted_systems:string;
  links:{jira:string;confluence:string;figma:string;drawio:string;bi:string}; files:string[]
}
const emptyInput:ContextInput={initiative_name:'',idea_summary:'',business_context:'',pain_points:'',impacted_processes:'',impacted_systems:'',links:{jira:'',confluence:'',figma:'',drawio:'',bi:''},files:[]}

const tabs:{label:string;type:ArtifactType;desc:string}[]=[
{label:'Контекст',type:'CONTEXT',desc:'Бизнес-контекст, цели и ограничения.'},{label:'Проблема',type:'PROBLEM',desc:'Проблема и её последствия.'},{label:'Цель',type:'GOAL',desc:'Целевая формулировка и критерии успеха.'},
{label:'Бизнес-эффект',type:'BUSINESS_EFFECT',desc:'Качественные и количественные эффекты.'},{label:'AS IS',type:'AS_IS',desc:'Текущее состояние.'},{label:'TO BE',type:'TO_BE',desc:'Целевое состояние.'},
{label:'Use Cases',type:'USE_CASES',desc:'Ключевые сценарии пользователей.'},{label:'Требования',type:'FUNCTIONAL_REQUIREMENTS',desc:'Функциональные требования.'},{label:'Риски',type:'RISKS',desc:'Риски и меры.'},{label:'Финальный БТ',type:'FINAL_BT',desc:'Финальная бизнес-требование спецификация.'}]

export default function ProjectPage(){
  const {projectId}=useParams(); const navigate = useNavigate(); const [searchParams] = useSearchParams(); const [project,setProject]=useState<Project|null>(null); const [active,setActive]=useState<ArtifactType>('CONTEXT')
  const [content,setContent]=useState(''); const [richJson,setRichJson]=useState<any>(null); const [structured,setStructured]=useState<any>({}); const [ver,setVer]=useState<number|null>(null); const [updated,setUpdated]=useState('');
  const [cmp,setCmp]=useState<any>(null); const [msg,setMsg]=useState(''); const [busy,setBusy]=useState(false); const [saving,setSaving]=useState<'idle'|'saving'|'saved'|'error'>('idle');
  const [contextInput,setContextInput]=useState<ContextInput>(emptyInput); const [analysis,setAnalysis]=useState<any>(null); const [thinking,setThinking]=useState(false)
  const current=tabs.find(t=>t.type===active)

  const loadCompletion=async()=>setCmp(await api<any>(`/projects/${projectId}/completion`).catch(()=>null))
  const load=async()=>{try{setProject(await api<Project>(`/projects/${projectId}`)); await loadCompletion()}catch{setMsg('Проект не найден')}}
  const loadArtifact=async(type:ArtifactType)=>{try{const a=await api<any>(`/projects/${projectId}/artifacts/${type}`);setContent(a.rendered_html||a.content||'');setRichJson(a.rich_content_json||null);setStructured(a.structured_content||{});setVer(a.version);setUpdated(a.updated_at); if(type==='CONTEXT'){setContextInput(a.structured_content?.context_input||emptyInput); setAnalysis(a.structured_content?.ai_analysis||null)}}catch{setContent('');setRichJson(null);setStructured({});setVer(null);setUpdated(''); if(type==='CONTEXT'){setContextInput(emptyInput); setAnalysis(null)}}}
  useEffect(()=>{load(); if(projectId) localStorage.setItem('lastOpenedProjectId', projectId)},[projectId]);
  useEffect(()=>{const st = searchParams.get('stage') as ArtifactType | null; if(st && tabs.some(t=>t.type===st)) setActive(st)},[searchParams]);
  useEffect(()=>{loadArtifact(active); if(projectId) navigate(`/projects/${projectId}?stage=${active}`, { replace:true })},[active,projectId])

  const save=async()=>{try{setSaving('saving');const payload=active==='GOAL'?{content:smartToText(structured),structured_content:structured,rich_content_json:richJson,rendered_html:content}:{content,structured_content:null,rich_content_json:richJson,rendered_html:content}; const a=await api<any>(`/projects/${projectId}/artifacts/${active}`,{method:'PUT',body:JSON.stringify(payload)});setVer(a.version);setUpdated(a.updated_at);setMsg('Сохранено');setSaving('saved');await loadCompletion()}catch{setMsg('Ошибка сохранения');setSaving('error')}}
  const gen=async()=>{try{setBusy(true);const a=await api<any>(`/projects/${projectId}/generate/${active}`,{method:'POST'});setContent(a.content);setStructured({});setVer(a.version);setUpdated(a.updated_at);setMsg('Генерация завершена');await loadCompletion()}catch{setMsg('Ошибка сохранения')}finally{setBusy(false)}}
  const validate=async()=>{try{setBusy(true);await api<any>(`/projects/${projectId}/validate`,{method:'POST'});setMsg('Сохранено');await loadCompletion()}catch{setMsg('Ошибка сохранения')}finally{setBusy(false)}}
  useEffect(()=>{if(active==='GOAL' || active==='CONTEXT') return; if(!content) return; const t=setTimeout(()=>{save()},2000); return ()=>clearTimeout(t)},[content])
  useEffect(()=>{if(active!=='CONTEXT') return; const t=setTimeout(()=>{saveContextInput()},1000); return ()=>clearTimeout(t)},[contextInput])


  const saveContextInput=async()=>{try{setSaving('saving'); await api<any>(`/projects/${projectId}/artifacts/CONTEXT`,{method:'PUT',body:JSON.stringify({content:analysis?.summary||content||'',structured_content:{context_input:contextInput,ai_analysis:analysis,analysis_history:structured?.analysis_history||[]}})}); setSaving('saved')}catch{setSaving('error')}}
  const runContextAnalyze=async()=>{try{setThinking(true); const r=await api<any>(`/projects/${projectId}/context/analyze`,{method:'POST',body:JSON.stringify({context_input:contextInput})}); setAnalysis(r.analysis); setMsg('AI-анализ обновлен'); await loadArtifact('CONTEXT')}catch{setMsg('Ошибка AI-анализа')}finally{setThinking(false)}}
  const copyTxt=(v:any)=>navigator.clipboard?.writeText(typeof v==='string'?v:JSON.stringify(v,null,2))

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
          <div><Link to='/' className='btn'>← К списку проектов</Link><h2 style={{margin:'10px 0 4px'}}>{current?.label}</h2><p className='sub' style={{margin:0}}>{current?.desc}</p></div>
          <div style={{display:'flex',alignItems:'center',gap:8,flexWrap:'wrap'}}><span className='sub'>Версия: {ver??0}</span><span className='sub'>Обновлено: {updated?new Date(updated).toLocaleString('ru-RU'):'—'}</span><button className='btn primary' onClick={save}>Сохранить</button><button className='btn' onClick={gen} disabled={busy}>Сгенерировать</button><button className='btn' onClick={validate} disabled={busy}>Проверить</button><a className='btn' href={`http://localhost:8000/api/projects/${projectId}/export/docx`}><Download size={16}/></a><button className='btn'><MoreHorizontal size={16}/></button></div>
        </div>

        {active==='CONTEXT' ? <div className='context-workspace'>
          <div className='context-left card'>
            <h4>Input / Source Data</h4>
            <input className='input' placeholder='Название инициативы' value={contextInput.initiative_name} onChange={e=>setContextInput({...contextInput,initiative_name:e.target.value})}/>
            <textarea className='textarea' placeholder='Краткое описание идеи' value={contextInput.idea_summary} onChange={e=>setContextInput({...contextInput,idea_summary:e.target.value})}/>
            <textarea className='textarea' placeholder='Бизнес-контекст' value={contextInput.business_context} onChange={e=>setContextInput({...contextInput,business_context:e.target.value})}/>
            <textarea className='textarea' placeholder='Что болит сейчас' value={contextInput.pain_points} onChange={e=>setContextInput({...contextInput,pain_points:e.target.value})}/>
            <input className='input' placeholder='Какие процессы затронуты' value={contextInput.impacted_processes} onChange={e=>setContextInput({...contextInput,impacted_processes:e.target.value})}/>
            <input className='input' placeholder='Какие системы затронуты' value={contextInput.impacted_systems} onChange={e=>setContextInput({...contextInput,impacted_systems:e.target.value})}/>
          </div>
          <div className='context-center card'>
            <div style={{display:'flex',justifyContent:'space-between'}}><h4>AI Workspace</h4><button className='btn primary' onClick={runContextAnalyze} disabled={thinking}>{thinking?'AI думает...':'Обновить AI-анализ'}</button></div>
            {!analysis && <p className='sub'>Заполните входные данные и запустите анализ.</p>}
            {analysis && <div className='ai-sections'>
              <div className='card'><b>AI Summary</b><p>{analysis.summary}</p></div>
              <div className='card'><b>AI Questions</b><ul>{(analysis.questions||[]).map((q:string,i:number)=><li key={i}>{q}</li>)}</ul></div>
              <div className='card'><b>AI Detected Entities</b><div className='timeline'>{[...(analysis.systems||[]),...(analysis.processes||[]),...(analysis.stakeholders||[])].map((x:string,i:number)=><span key={i} className='chip in_progress'>{x}</span>)}</div></div>
              <div className='card'><b>AI Risks</b><ul>{(analysis.risks||[]).map((r:string,i:number)=><li key={i}>{r}</li>)}</ul></div>
              <div className='card'><b>AI Recommendations</b><ul>{(analysis.recommendations||[]).map((r:string,i:number)=><li key={i}>{r}</li>)}</ul></div>
              <div className='card'><b>Context completeness: {analysis.completeness_score||0}%</b><div className='progress'><div style={{width:`${analysis.completeness_score||0}%`}}/></div></div>
              <div className='card'><div style={{display:'flex',justifyContent:'space-between'}}><b>AI Generated Hypothesis</b><div><button className='btn' onClick={()=>copyTxt(analysis.hypothesis)}><Copy size={14}/></button><button className='btn' onClick={runContextAnalyze}><RefreshCcw size={14}/></button></div></div><p>{analysis.hypothesis}</p></div>
            </div>}
          </div>
          <div className='context-right card'>
            <h4>Artifacts & History</h4>
            <div className='sub'>История AI-анализов: {(structured?.analysis_history||[]).length}</div>
            <div className='sub'>Последние изменения: {updated?new Date(updated).toLocaleString('ru-RU'):'—'}</div>
            <div className='sub'>Загруженные файлы: {contextInput.files.length}</div>
          </div>
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
        <div className='sub'>Autosave: {saving==='saving'?'Сохранение…':saving==='saved'?'Сохранено':saving==='error'?'Ошибка сохранения':'—'}</div>
        {msg && <p className={`sub ${msg==='Сохранено' || msg==='Генерация завершена' ? '' : ''}`}>{msg}</p>}
      </div>
    </section>
  </div>
}
