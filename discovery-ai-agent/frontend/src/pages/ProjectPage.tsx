import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { api } from '../api/client'
import { ArtifactType, Project } from '../types/discovery'

const tabs:{label:string;type:ArtifactType;generationType?:ArtifactType;required?:boolean}[]=[
{label:'Контекст',type:'CONTEXT',required:true},{label:'Проблема',type:'PROBLEM',generationType:'PROBLEM',required:true},{label:'Цель',type:'GOAL',generationType:'GOAL',required:true},
{label:'Бизнес-эффект',type:'BUSINESS_EFFECT',generationType:'BUSINESS_EFFECT',required:true},{label:'AS IS',type:'AS_IS',required:true},{label:'TO BE',type:'TO_BE',required:true},
{label:'Use Cases',type:'USE_CASES',generationType:'USE_CASES',required:true},{label:'Требования',type:'FUNCTIONAL_REQUIREMENTS',generationType:'FUNCTIONAL_REQUIREMENTS',required:true},
{label:'Риски',type:'RISKS',required:true},{label:'Финальный БТ',type:'FINAL_BT',generationType:'FINAL_BT'}]

export default function ProjectPage(){
const {projectId}=useParams(); const [project,setProject]=useState<Project|null>(null); const [active,setActive]=useState<ArtifactType>('CONTEXT')
const [content,setContent]=useState(''); const [structured,setStructured]=useState<any>({}); const [version,setVersion]=useState<number|null>(null)
const [busy,setBusy]=useState(false); const [error,setError]=useState(''); const [mode,setMode]=useState<'structured'|'free'>('structured'); const [completion,setCompletion]=useState<any>(null)
const currentTab=tabs.find(t=>t.type===active); const canGenerate=Boolean(currentTab?.generationType)
const loadProject=async()=>setProject(await api<Project>(`/projects/${projectId}`))
const loadCompletion=async()=>setCompletion(await api<any>(`/projects/${projectId}/completion`))
const loadArtifact=async(type:ArtifactType)=>{try{const a=await api<any>(`/projects/${projectId}/artifacts/${type}`);setContent(a.content||'');setStructured(a.structured_content||{});setVersion(a.version)}catch{setContent('');setStructured({});setVersion(null)}}
useEffect(()=>{loadProject();loadCompletion()},[projectId]); useEffect(()=>{loadArtifact(active)},[active,projectId])
const save=async()=>{try{setError('');const a=await api<any>(`/projects/${projectId}/artifacts/${active}`,{method:'PUT',body:JSON.stringify({content,structured_content:structured})});setVersion(a.version);loadCompletion()}catch{setError('Ошибка сохранения')}}
const gen=async()=>{if(!currentTab?.generationType)return;try{setBusy(true);const a=await api<any>(`/projects/${projectId}/generate/${currentTab.generationType}`,{method:'POST'});setContent(a.content);setStructured({});setVersion(a.version);loadCompletion()}catch{setError('Ошибка генерации')}finally{setBusy(false)}}
const validate=async()=>{try{setBusy(true);await api<any>(`/projects/${projectId}/validate`,{method:'POST'});setError('Проверка завершена');loadCompletion()}catch{setError('Ошибка проверки')}finally{setBusy(false)}}

const bind=(k:string)=><input value={structured[k]||''} onChange={e=>setStructured({...structured,[k]:e.target.value})} style={{width:'100%',marginBottom:8}}/>
const bindList=(k:string)=><textarea value={(structured[k]||[]).join('\n')} onChange={e=>setStructured({...structured,[k]:e.target.value.split('\n').filter(Boolean)})} style={{width:'100%',minHeight:70,marginBottom:8}}/>

const renderForm=()=>{if(active==='PROBLEM') return <>{bind('problem_statement')}{bindList('causes')}{bindList('consequences')}{bindList('affected_users')}{bind('change_reason')}{bindList('open_questions')}</>
if(active==='GOAL') return <>{bind('goal_text')}{bind('specific')}{bind('measurable')}{bind('achievable')}{bind('relevant')}{bind('time_bound')}</>
if(active==='BUSINESS_EFFECT') return <>{bindList('qualitative_effects')}{bindList('quantitative_metrics')}{bind('expected_result')}</>
if(active==='FUNCTIONAL_REQUIREMENTS') return <>{bindList('functional_requirements')}{bindList('non_functional_requirements')}{bindList('business_rules')}{bindList('acceptance_criteria')}</>
if(active==='RISKS') return <textarea value={(structured.risks||[]).map((r:any)=>`${r.risk}|${r.impact}|${r.mitigation}`).join('\n')} onChange={e=>setStructured({...structured,risks:e.target.value.split('\n').filter(Boolean).map(x=>{const [risk,impact,mitigation]=x.split('|'); return {risk:risk||'',impact:impact||'',mitigation:mitigation||''}})})} style={{width:'100%',minHeight:120}}/>
if(active==='USE_CASES') return <textarea value={JSON.stringify(structured.use_cases||[],null,2)} onChange={e=>{try{setStructured({...structured,use_cases:JSON.parse(e.target.value)})}catch{}}} style={{width:'100%',minHeight:220}}/>
return <p>Для этой вкладки используйте режим свободного текста.</p>}

if(!project)return <div style={{padding:24}}>Loading...</div>
return <div style={{display:'flex',gap:16,padding:16,fontFamily:'Arial'}}>
<div style={{width:260,border:'1px solid #ddd',padding:12}}>
<h4>Этапы</h4>{tabs.map(t=>{const st=completion?.sections?.find((s:any)=>s.artifact_type===t.type);return <div key={t.type} onClick={()=>setActive(t.type)} style={{cursor:'pointer',padding:6,background:active===t.type?'#eef':'transparent'}}>{t.label} <span style={{color:st?.is_completed?'green':'#999'}}>{st?.is_completed?'●':'○'}</span></div>})}
</div>
<div style={{flex:1}}>
<h2>{project.project_name}</h2>
<div style={{border:'1px solid #ddd',padding:10,marginBottom:10}}>
<b>Прогресс: {completion?.completion_percent ?? 0}%</b>
<div>Обязательные разделы: {completion?.required_sections_completed ?? 0}/{completion?.required_sections_total ?? 0}</div>
<div>{(completion?.missing_sections||[]).join(', ')}</div>
</div>
<div><button onClick={()=>setMode('structured')}>Структурированная форма</button><button onClick={()=>setMode('free')} style={{marginLeft:8}}>Свободный текст</button></div>
<div style={{marginTop:10}}>{mode==='structured'?renderForm():<textarea value={content} onChange={e=>setContent(e.target.value)} style={{width:'100%',minHeight:260}}/>}</div>
<div style={{marginTop:8}}><button onClick={save}>Сохранить</button><button onClick={gen} disabled={!canGenerate||busy} style={{marginLeft:8}}>{busy?'Генерация...':'Сгенерировать'}</button><button onClick={validate} style={{marginLeft:8}}>Проверить</button><button disabled style={{marginLeft:8}}>Сформировать БТ</button><span style={{marginLeft:8}}>Версия: {version??'—'}</span></div>
{error && <p>{error}</p>}
</div></div>}
