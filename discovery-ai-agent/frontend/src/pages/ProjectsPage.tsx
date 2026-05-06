import { Plus } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import { Project } from '../types/discovery'

export default function ProjectsPage(){
  const navigate = useNavigate()
  const [projects,setProjects]=useState<Project[]>([]); const [name,setName]=useState(''); const [q,setQ]=useState(''); const [status,setStatus]=useState('ALL');
  const load=async()=>setProjects(await api<Project[]>('/projects').catch(()=>[]))
  useEffect(()=>{load()},[])
  const create=async()=>{if(!name.trim()) return; await api('/projects',{method:'POST',body:JSON.stringify({project_name:name})}); setName(''); load()}
  const filtered = useMemo(()=>projects.filter(p=>(status==='ALL'||p.status===status)&&p.project_name.toLowerCase().includes(q.toLowerCase())),[projects,q,status])
  const del=async(id:string)=>{await api(`/projects/${id}`,{method:'DELETE'}); load()}

  return <div>
    <h1 className='page-title'>Проекты</h1>
    <div className='card' style={{display:'grid',gap:8,marginBottom:12}}>
      <div style={{display:'flex',gap:8}}><input className='input' placeholder='Поиск' value={q} onChange={e=>setQ(e.target.value)} /><select className='input' value={status} onChange={e=>setStatus(e.target.value)}><option value='ALL'>Все</option><option value='DRAFT'>DRAFT</option><option value='IN_PROGRESS'>IN_PROGRESS</option><option value='BT_READY'>BT_READY</option><option value='APPROVED'>APPROVED</option></select></div>
      <div style={{display:'flex',gap:8}}><input className='input' placeholder='Название проекта' value={name} onChange={e=>setName(e.target.value)} /><button className='btn primary' onClick={create}><Plus size={16}/>Создать проект</button></div>
    </div>
    <div className='card'>
      <table style={{width:'100%'}}><thead><tr><th align='left'>Название</th><th align='left'>Статус</th><th align='left'>Действия</th></tr></thead><tbody>
      {filtered.map(p=><tr key={p.id}><td>{p.project_name}</td><td>{p.status}</td><td style={{display:'flex',gap:6,flexWrap:'wrap'}}>
        <button className='btn' onClick={()=>navigate(`/projects/${p.id}`)}>Открыть</button>
        <button className='btn' onClick={()=>api('/projects',{method:'POST',body:JSON.stringify({project_name:`${p.project_name} (копия)`})}).then(load)}>Клонировать</button>
        <button className='btn' onClick={()=>api(`/projects/${p.id}`,{method:'PATCH',body:JSON.stringify({status:'DRAFT'})}).then(load)}>Архивировать</button>
        <a className='btn' href={`http://localhost:8000/api/projects/${p.id}/export/docx`}>Экспорт</a>
        <button className='btn' onClick={()=>del(p.id)}>Удалить</button>
      </td></tr>)}
      </tbody></table>
    </div>
  </div>
}
