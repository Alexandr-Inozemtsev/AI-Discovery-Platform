import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api } from '../api/client'
import { ArtifactType, Project } from '../types/discovery'

const tabs:{label:string;type:ArtifactType;desc:string}[]=[
{label:'Контекст',type:'CONTEXT',desc:'Бизнес-контекст, цели и ограничения.'},{label:'Проблема',type:'PROBLEM',desc:'Проблема и её последствия.'},{label:'Цель',type:'GOAL',desc:'Целевая формулировка и критерии успеха.'},
{label:'Бизнес-эффект',type:'BUSINESS_EFFECT',desc:'Качественные и количественные эффекты.'},{label:'AS IS',type:'AS_IS',desc:'Текущее состояние.'},{label:'TO BE',type:'TO_BE',desc:'Целевое состояние.'},
{label:'Use Cases',type:'USE_CASES',desc:'Ключевые сценарии пользователей.'},{label:'Требования',type:'FUNCTIONAL_REQUIREMENTS',desc:'Функциональные требования.'},{label:'Риски',type:'RISKS',desc:'Риски и меры.'},{label:'Финальный БТ',type:'FINAL_BT',desc:'Финальная бизнес-требование спецификация.'}]

export default function ProjectPage(){
  const {projectId}=useParams(); const [project,setProject]=useState<Project|null>(null); const [active,setActive]=useState<ArtifactType>('CONTEXT'); const [content,setContent]=useState(''); const [ver,setVer]=useState<number|null>(null); const [updated,setUpdated]=useState(''); const [cmp,setCmp]=useState<any>(null); const [msg,setMsg]=useState(''); const [busy,setBusy]=useState(false)
  const current=tabs.find(t=>t.type===active)
  const loadCompletion=async()=>setCmp(await api<any>(`/projects/${projectId}/completion`).catch(()=>null))
  const load=async()=>{try{setProject(await api<Project>(`/projects/${projectId}`)); await loadCompletion()}catch{setMsg('Проект не найден')}}
  const loadArtifact=async(type:ArtifactType)=>{try{const a=await api<any>(`/projects/${projectId}/artifacts/${type}`);setContent(a.content||'');setVer(a.version);setUpdated(a.updated_at)}catch{setContent('');setVer(null);setUpdated('')}}
  useEffect(()=>{load()},[projectId]); useEffect(()=>{loadArtifact(active)},[active,projectId])
  const saveProject=async()=>{try{await api(`/projects/${projectId}`,{method:'PATCH',body:JSON.stringify({project_name:project?.project_name,business_domain:(project as any)?.business_domain,jira_epic_url:(project as any)?.jira_epic_url})});setMsg('Проект успешно сохранён')}catch{setMsg('Backend недоступен. Проверьте, что FastAPI запущен на http://localhost:8000')}}
  const save=async()=>{try{const a=await api<any>(`/projects/${projectId}/artifacts/${active}`,{method:'PUT',body:JSON.stringify({content})}); setVer(a.version); setUpdated(a.updated_at); setMsg('Артефакт сохранён'); await loadCompletion()}catch{setMsg('Ошибка сохранения')}}
  const gen=async()=>{try{setBusy(true);const a=await api<any>(`/projects/${projectId}/generate/${active}`,{method:'POST'});setContent(a.content);setVer(a.version);setUpdated(a.updated_at);setMsg('Генерация завершена'); await loadCompletion()}catch{setMsg('Ошибка генерации')}finally{setBusy(false)}}
  const validate=async()=>{try{setBusy(true);await api<any>(`/projects/${projectId}/validate`,{method:'POST'});setMsg('Проверка завершена'); await loadCompletion()}catch{setMsg('Ошибка проверки')}finally{setBusy(false)}}

  if(!project)return <div className='card'>Проект не найден</div>
  return <div>
    <div className='card' style={{marginBottom:12}}><div style={{display:'flex',justifyContent:'space-between',alignItems:'center',gap:8,flexWrap:'wrap'}}><Link to='/' className='btn'>← К списку проектов</Link><div className='sub'>Общая заполненность: <b>{cmp?.completion_percent ?? 0}%</b></div><button className='btn primary' onClick={saveProject}>Сохранить</button></div>
      <div style={{display:'grid',gridTemplateColumns:'repeat(2,minmax(0,1fr))',gap:8,marginTop:10}}><input className='input' value={project.project_name} onChange={e=>setProject({...project,project_name:e.target.value})}/><input className='input' value={(project as any).business_domain||''} onChange={e=>setProject({...project,business_domain:e.target.value} as any)} placeholder='Бизнес-направление'/><input className='input' value={(project as any).jira_epic_url||''} onChange={e=>setProject({...project,jira_epic_url:e.target.value} as any)} placeholder='Jira Epic URL'/><div className='card' style={{padding:10}}>Статус: {(project as any).status} · Этап: {(project as any).current_stage}</div></div>
    </div>

    <div className='card' style={{marginBottom:12}}><h3 style={{marginTop:0}}>Discovery Progress Timeline</h3><div className='timeline'>{tabs.map(t=>{const s=cmp?.sections?.find((x:any)=>x.artifact_type===t.type)?.status||'not_started'; return <span key={t.type} className={`chip ${s}`}>{t.label}</span>})}</div></div>

    <div className='layout'>
      <aside className='card'><h3 style={{marginTop:0}}>Этапы</h3>{tabs.map(t=>{const s=cmp?.sections?.find((x:any)=>x.artifact_type===t.type); return <div key={t.type} className={`sidebar-item ${active===t.type?'active':''}`} onClick={()=>setActive(t.type)}><span>{t.label}</span><span className={`chip ${s?.status||'not_started'}`}>{s?.status==='completed'?'✓':s?.status==='in_progress'?'~':'·'}</span></div>})}</aside>
      <section className='card'><h2 style={{marginTop:0}}>{current?.label}</h2><p className='sub'>{current?.desc}</p><textarea className='textarea' value={content} onChange={e=>setContent(e.target.value)} /><div style={{display:'flex',gap:8,alignItems:'center',marginTop:10,flexWrap:'wrap'}}><button className='btn primary' onClick={save}>Сохранить</button><button className='btn' onClick={gen} disabled={busy}>{busy?'Генерация...':'Сгенерировать'}</button><button className='btn' onClick={validate} disabled={busy}>Проверить</button><span style={{marginLeft:'auto'}}>Версия: {ver??'—'}</span></div><div className='sub'>Последнее изменение: {updated?new Date(updated).toLocaleString('ru-RU'):'—'}</div>{msg && <p>{msg}</p>}</section>
    </div>
  </div>
}
