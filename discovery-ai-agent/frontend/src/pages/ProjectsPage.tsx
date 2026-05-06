import { BarChart3, CheckCircle2, Clock3, FolderPlus, Plus, Rocket, UserCircle2 } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import { Project } from '../types/discovery'

const stages = ['Контекст','Проблема','Цель','Бизнес-эффект','AS IS','TO BE','Use Cases','Требования','Риски','Финальный БТ']

export default function ProjectsPage(){
  const navigate = useNavigate()
  const [projects,setProjects]=useState<Project[]>([]); const [name,setName]=useState(''); const [msg,setMsg]=useState(''); const [cmp,setCmp]=useState<Record<string,any>>({})
  const load=async()=>{try{const p=await api<Project[]>('/projects'); setProjects(p); const arr=await Promise.all(p.map(async x=>[x.id,await api<any>(`/projects/${x.id}/completion`).catch(()=>({completion_percent:0,sections:[]}))] as const)); setCmp(Object.fromEntries(arr))}catch{setMsg('Backend недоступен. Проверьте, что FastAPI запущен на http://localhost:8000')}}
  useEffect(()=>{load()},[])
  const create=async()=>{if(!name.trim()) return setMsg('Укажите название проекта'); try{await api('/projects',{method:'POST',body:JSON.stringify({project_name:name})}); setName(''); setMsg('Проект успешно создан'); load()}catch{setMsg('Ошибка создания проекта')}}
  const stats=useMemo(()=>({total:projects.length,inwork:projects.filter(p=>p.status==='IN_PROGRESS').length,ready:projects.filter(p=>p.status==='BT_READY').length,avg:projects.length?Math.round(projects.reduce((a,p)=>a+(cmp[p.id]?.completion_percent||0),0)/projects.length):0}),[projects,cmp])

  return <div>
    <h1 className='page-title'>Добро пожаловать, Александр 👋</h1>
    <p className='sub' style={{marginTop:0}}>Рабочее пространство для Discovery и подготовки бизнес-требований</p>

    <div className='home-top'>
      <div className='kpi-grid'>
        {[['Всего проектов',stats.total,FolderPlus,'#dbeafe'],['В работе',stats.inwork,Clock3,'#fef3c7'],['БТ готовы',stats.ready,CheckCircle2,'#dcfce7'],['Средняя заполненность',`${stats.avg}%`,BarChart3,'#e0e7ff']].map(([t,v,Icon,bg]:any)=><div className='card kpi' key={t}><div className='kpi-icon' style={{background:bg}}><Icon size={18}/></div><div className='kpi-value'>{v}</div><div className='sub'>{t}</div></div>)}
      </div>
      <div className='cta-card'>
        <div><div className='sub' style={{color:'#bfdbfe'}}>Новый старт</div><h3>Создать новый проект</h3><p>Начните новый Discovery-проект</p></div>
        <button className='btn' onClick={create}><Plus size={16}/> Создать <Rocket size={16}/></button>
        <input className='input' placeholder='Название проекта' value={name} onChange={e=>setName(e.target.value)} />
      </div>
    </div>

    <div className='card' style={{marginBottom:16}}>
      <div style={{display:'flex',justifyContent:'space-between',gap:8,alignItems:'center',flexWrap:'wrap'}}><h3 style={{margin:0}}>Этапы Discovery</h3><button className='btn primary' onClick={()=>{if(projects[0]) navigate(`/projects/${projects[0].id}?stage=CONTEXT`); else setMsg('Сначала создайте или откройте проект')}}>Открыть рабочее пространство →</button></div>
      <div className='pipeline'>{stages.map((s,i)=>{const st=i<3?'completed':i<6?'in_progress':'not_started'; const map:any={'Контекст':'CONTEXT','Проблема':'PROBLEM','Цель':'GOAL','Бизнес-эффект':'BUSINESS_EFFECT','AS IS':'AS_IS','TO BE':'TO_BE','Use Cases':'USE_CASES','Требования':'FUNCTIONAL_REQUIREMENTS','Риски':'RISKS','Финальный БТ':'FINAL_BT'}; return <button key={s} className='pipe-item' onClick={()=>{if(projects[0]) navigate(`/projects/${projects[0].id}?stage=${map[s]}`); else setMsg('Сначала создайте или откройте проект')}}><span className={`dot ${st}`}>{st==='completed'?'✓':''}</span><span>{s}</span></button>})}</div>
      <div className='legend'><span><i className='dot completed'/>Заполнено</span><span><i className='dot in_progress'/>В работе</span><span><i className='dot not_started'/>Не начато</span></div>
    </div>

    <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',margin:'10px 0'}}><h3>Проекты</h3><div className='sub'>Сортировка: Последнее обновление · Вид: Карточки ⬚⬚</div></div>

    {projects.length===0 ? <div className='card empty'><h3>Пока нет Discovery-проектов</h3><p className='sub'>Создайте первый проект, чтобы начать работу</p></div> :
    <div className='gridCards'>{projects.map(p=>{const c=cmp[p.id]||{completion_percent:0,sections:[]}; const completed=(c.sections||[]).filter((x:any)=>x.status==='completed').length; return <Link to={`/projects/${p.id}`} key={p.id} className='card project-card'>
      <div style={{display:'flex',justifyContent:'space-between',gap:8}}><h3 style={{margin:'0 0 6px 0'}}>{p.project_name}</h3><span className='badge'>{p.status}</span></div>
      <div className='sub'>Бизнес-направление: {(p as any).business_domain || '—'}</div>
      <div className='sub'>Обновлено: {new Date((p as any).updated_at).toLocaleString('ru-RU')}</div>
      <div className='progress'><div style={{width:`${c.completion_percent}%`}}/></div>
      <div style={{display:'flex',justifyContent:'space-between',marginTop:8}}><b>{c.completion_percent}%</b><span className='sub'>Этапов: {completed}/{stages.length}</span><span className='sub'>Версия: v{Math.max(...(c.sections||[]).map((x:any)=>x.version||0),0)}</span></div>
      <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',marginTop:8}}><span className='sub'><UserCircle2 size={14}/> Александр</span><span className='sub'>Открыть →</span></div>
    </Link>})}</div>}

    {msg && <p>{msg}</p>}
  </div>
}
