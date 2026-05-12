import { Activity, AlertTriangle, ArrowRight, BarChart3, CheckCheck, Clock3, FileDown, FileUp, Lightbulb, PlayCircle, PlusCircle } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import { Project } from '../types/discovery'
import Card from '../ui/components/Card'
import Button from '../ui/components/Button'
import ButtonLink from '../ui/components/ButtonLink'
import PageContainer from '../ui/components/PageContainer'

export default function HomePage() {
  const navigate = useNavigate(); const [projects, setProjects] = useState<Project[]>([]); const [completion, setCompletion] = useState<Record<string, any>>({})
  useEffect(() => { (async()=>{const p = await api<Project[]>('/projects').catch(() => []); setProjects(p); const cmp = await Promise.all(p.slice(0,8).map(async x=>[x.id, await api<any>(`/projects/${x.id}/completion`).catch(()=>({completion_percent:0,missing_sections:[]}))] as const)); setCompletion(Object.fromEntries(cmp))})() }, [])
  const last = projects[0]
  const stats = useMemo(() => {const total=projects.length,inwork=projects.filter(p=>p.status==='IN_PROGRESS').length,done=projects.filter(p=>p.status==='BT_READY'||p.status==='APPROVED').length,avg=total?Math.round(projects.reduce((a,p)=>a+(completion[p.id]?.completion_percent||0),0)/total):0,gaps=projects.reduce((a,p)=>a+((completion[p.id]?.missing_sections||[]).length||0),0); return { total,inwork,done,avg,aiNotes:inwork+done,gaps}}, [projects,completion])
  return <PageContainer>
    <h1 className='page-title'>Главная</h1>
    <div className='kpi-grid'>{[['Всего проектов', stats.total], ['В работе', stats.inwork], ['Завершено', stats.done], ['Средняя готовность', `${stats.avg}%`], ['AI-замечания', stats.aiNotes], ['Незаполненные разделы', stats.gaps]].map(([t, v]) => <Card className='kpi' key={String(t)}><div className='kpi-value'>{v}</div><div className='sub'>{t}</div></Card>)}</div>
    <div className='gridCards' style={{ marginTop: 14 }}>
      <Card><h3>Продолжить работу</h3><p className='sub'>{last ? last.project_name : 'Нет активного проекта'}</p>{last && <Button variant='primary' onClick={() => navigate(`/projects/${last.id}`)}><PlayCircle size={16} /> Открыть</Button>}</Card>
      <Card><h3>Быстрые действия</h3><div style={{ display: 'grid', gap: 8 }}><ButtonLink variant='secondary' to='/projects'><PlusCircle size={16} /> Создать проект</ButtonLink><Button><FileUp size={16} /> Импортировать БТ</Button><Button onClick={() => last && navigate(`/projects/${last.id}`)}><Clock3 size={16} /> Продолжить последний проект</Button><Button><CheckCheck size={16} /> Проверить полноту</Button><Button><FileDown size={16} /> Экспортировать БТ</Button></div></Card>
      <Card><h3>AI рекомендации</h3><p className='sub'><Lightbulb size={14} /> Добавьте SMART-критерии в цели для повышения заполненности.</p><p className='sub'><AlertTriangle size={14} /> Проверьте разделы с коротким текстом (&lt; 50 символов).</p></Card>
      <Card><h3>Последние проекты</h3>{projects.slice(0, 5).map(p => <div key={p.id} className='sub'>{p.project_name} <ArrowRight size={12} /></div>)}</Card>
      <Card><h3>Последние изменения</h3><p className='sub'><Activity size={14} /> Изменения доступны в карточках проектов.</p><p className='sub'><BarChart3 size={14} /> Следите за динамикой заполненности.</p></Card>
    </div>
  </PageContainer>
}
