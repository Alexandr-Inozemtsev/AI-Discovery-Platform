import { Plus } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import Card from '../ui/components/Card'
import Button from '../ui/components/Button'
import ButtonLink from '../ui/components/ButtonLink'
import Input from '../ui/components/Input'
import PageContainer from '../ui/components/PageContainer'
import { Project } from '../types/discovery'

export default function ProjectsPage(){
  const navigate = useNavigate()
  const [projects,setProjects]=useState<Project[]>([]); const [name,setName]=useState(''); const [q,setQ]=useState(''); const [status,setStatus]=useState('ALL');
  const load=async()=>setProjects(await api<Project[]>('/projects').catch(()=>[]))
  useEffect(()=>{load()},[])
  const create=async()=>{if(!name.trim()) return; await api('/projects',{method:'POST',body:JSON.stringify({project_name:name})}); setName(''); load()}
  const filtered = useMemo(()=>projects.filter(p=>(status==='ALL'||p.status===status)&&p.project_name.toLowerCase().includes(q.toLowerCase())),[projects,q,status])
  const del=async(id:string)=>{await api(`/projects/${id}`,{method:'DELETE'}); load()}

  return <PageContainer>
    <h1 className='page-title'>Проекты</h1>
    <Card className='projects-filter'>
      <div className='ui-actions'><Input placeholder='Поиск' value={q} onChange={e=>setQ(e.target.value)} /><select className='ui-input' value={status} onChange={e=>setStatus(e.target.value)}><option value='ALL'>Все</option><option value='DRAFT'>DRAFT</option><option value='IN_PROGRESS'>IN_PROGRESS</option><option value='BT_READY'>BT_READY</option><option value='APPROVED'>APPROVED</option></select></div>
      <div className='ui-actions'><Input placeholder='Название проекта' value={name} onChange={e=>setName(e.target.value)} /><Button variant='primary' onClick={create}><Plus size={16}/>Создать проект</Button></div>
    </Card>
    <Card>
      <table className='ui-table'><thead><tr><th align='left'>Название</th><th align='left'>Статус</th><th align='left'>Действия</th></tr></thead><tbody>
      {filtered.map(p=><tr key={p.id}><td>{p.project_name}</td><td><span className='ui-badge muted'>{p.status}</span></td><td className='ui-row-actions'>
        <Button onClick={()=>navigate(`/projects/${p.id}`)}>Открыть</Button>
        <Button onClick={()=>api('/projects',{method:'POST',body:JSON.stringify({project_name:`${p.project_name} (копия)`})}).then(load)}>Клонировать</Button>
        <Button onClick={()=>api(`/projects/${p.id}`,{method:'PATCH',body:JSON.stringify({status:'DRAFT'})}).then(load)}>Архивировать</Button>
        <ButtonLink variant='secondary' size='sm' href={`http://localhost:8000/api/projects/${p.id}/export/docx`}>Экспорт</ButtonLink>
        <Button onClick={()=>del(p.id)}>Удалить</Button>
      </td></tr>)}
      </tbody></table>
    </Card>
  </PageContainer>
}
