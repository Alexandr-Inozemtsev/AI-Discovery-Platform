import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import { Project } from '../types/discovery'

const pipeline = ['Контекст','Проблема','Цель','Бизнес-эффект','AS IS','TO BE','Use Cases','Требования','Риски','Финальный БТ']

export default function ProjectsPage(){
  const [projects,setProjects]=useState<Project[]>([]); const [name,setName]=useState(''); const [msg,setMsg]=useState(''); const [cmp,setCmp]=useState<Record<string,any>>({})
  const load=async()=>{try{const p=await api<Project[]>('/projects'); setProjects(p); const arr=await Promise.all(p.map(async x=>[x.id, await api<any>(`/projects/${x.id}/completion`).catch(()=>({completion_percent:0}))] as const)); setCmp(Object.fromEntries(arr))}catch{setMsg('Backend недоступен. Проверьте, что FastAPI запущен на http://localhost:8000')}}
  useEffect(()=>{load()},[])
  const create=async()=>{if(!name.trim())return; try{await api('/projects',{method:'POST',body:JSON.stringify({project_name:name})}); setName(''); setMsg('Проект создан'); load()}catch{setMsg('Ошибка создания проекта')}}
  const stats=useMemo(()=>({total:projects.length,inwork:projects.filter(p=>p.status==='IN_PROGRESS').length,ready:projects.filter(p=>p.status==='BT_READY').length,avg: projects.length?Math.round(projects.reduce((a,p)=>a+(cmp[p.id]?.completion_percent||0),0)/projects.length):0}),[projects,cmp])

  return <div>
    <section className='hero'><h1 style={{marginTop:0}}>Ускорьте Discovery и подготовку БТ</h1><p>Запускайте discovery-проекты, отслеживайте прогресс этапов и используйте mock-агентов для черновиков артефактов.</p><button className='btn primary' onClick={()=>document.getElementById('create')?.scrollIntoView({behavior:'smooth'})}>Создать Discovery-проект</button></section>
    <section className='grid4' style={{marginBottom:16}}>{[['Всего проектов',stats.total],['В работе',stats.inwork],['БТ готовы',stats.ready],['Средняя заполненность',`${stats.avg}%`]].map(([k,v])=><div className='card' key={String(k)}><div className='sub'>{k}</div><div style={{fontSize:28,fontWeight:700}}>{v}</div></div>)}</section>
    <section className='card' style={{marginBottom:16}}><h3 style={{marginTop:0}}>Этапы Discovery</h3><div className='timeline'>{pipeline.map((p,i)=><span key={p} className={`chip ${i<2?'completed':i<5?'in_progress':'not_started'}`}>{p}</span>)}</div></section>
    <section className='card' id='create' style={{marginBottom:16}}><h3 style={{marginTop:0}}>Новый проект</h3><div style={{display:'flex',gap:8}}><input className='input' placeholder='Название проекта' value={name} onChange={e=>setName(e.target.value)} /><button className='btn primary' onClick={create}>Создать проект</button></div>{msg && <p>{msg}</p>}</section>
    <section className='gridCards'>{projects.map(p=>{const pc=cmp[p.id]?.completion_percent||0; return <div className='card' key={p.id}><h3 style={{marginTop:0}}>{p.project_name}</h3><div className='sub'>Статус: {p.status}</div><div className='sub'>Этап: {p.current_stage}</div><div className='sub'>Заполненность: {pc}%</div><div className='progress' style={{margin:'8px 0'}}><div style={{width:`${pc}%`}}/></div><div className='sub'>Обновлён: {new Date((p as any).updated_at).toLocaleString('ru-RU')}</div><Link className='btn primary' to={`/projects/${p.id}`} style={{display:'inline-block',marginTop:10}}>Открыть</Link></div>})}</section>
  </div>
}
