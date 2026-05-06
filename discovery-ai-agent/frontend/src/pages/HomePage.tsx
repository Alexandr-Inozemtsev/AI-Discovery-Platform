import { Activity, AlertTriangle, ArrowRight, BarChart3, CheckCheck, Clock3, FileDown, FileUp, Lightbulb, PlayCircle, PlusCircle } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import { Project } from '../types/discovery'

export default function HomePage() {
  const navigate = useNavigate()
  const [projects, setProjects] = useState<Project[]>([])
  const [completion, setCompletion] = useState<Record<string, any>>({})

  useEffect(() => {
    const load = async () => {
      const p = await api<Project[]>('/projects').catch(() => [])
      setProjects(p)
      const cmp = await Promise.all(p.slice(0, 8).map(async x => [x.id, await api<any>(`/projects/${x.id}/completion`).catch(() => ({ completion_percent: 0, sections: [], missing_sections: [] }))] as const))
      setCompletion(Object.fromEntries(cmp))
    }
    load()
  }, [])

  const last = projects[0]
  const stats = useMemo(() => {
    const total = projects.length
    const inwork = projects.filter(p => p.status === 'IN_PROGRESS').length
    const done = projects.filter(p => p.status === 'BT_READY' || p.status === 'APPROVED').length
    const avg = total ? Math.round(projects.reduce((a, p) => a + (completion[p.id]?.completion_percent || 0), 0) / total) : 0
    const gaps = projects.reduce((a, p) => a + ((completion[p.id]?.missing_sections || []).length || 0), 0)
    return { total, inwork, done, avg, aiNotes: inwork + done, gaps }
  }, [projects, completion])

  return <div>
    <h1 className='page-title'>Главная</h1>
    <div className='kpi-grid'>
      {[['Всего проектов', stats.total], ['В работе', stats.inwork], ['Завершено', stats.done], ['Средняя готовность', `${stats.avg}%`], ['AI-замечания', stats.aiNotes], ['Незаполненные разделы', stats.gaps]].map(([t, v]) => (
        <div className='card kpi' key={String(t)}><div className='kpi-value'>{v}</div><div className='sub'>{t}</div></div>
      ))}
    </div>
    <div className='gridCards' style={{ marginTop: 14 }}>
      <div className='card'><h3>Продолжить работу</h3><p className='sub'>{last ? last.project_name : 'Нет активного проекта'}</p>{last && <button className='btn primary' onClick={() => navigate(`/projects/${last.id}`)}><PlayCircle size={16} /> Открыть</button>}</div>
      <div className='card'><h3>Быстрые действия</h3><div style={{ display: 'grid', gap: 8 }}>
        <Link className='btn' to='/projects'><PlusCircle size={16} /> Создать проект</Link>
        <button className='btn'><FileUp size={16} /> Импортировать БТ</button>
        <button className='btn' onClick={() => last && navigate(`/projects/${last.id}`)}><Clock3 size={16} /> Продолжить последний проект</button>
        <button className='btn'><CheckCheck size={16} /> Проверить полноту</button>
        <button className='btn'><FileDown size={16} /> Экспортировать БТ</button>
      </div></div>
      <div className='card'><h3>AI рекомендации</h3><p className='sub'><Lightbulb size={14} /> Добавьте SMART-критерии в цели для повышения заполненности.</p><p className='sub'><AlertTriangle size={14} /> Проверьте разделы с коротким текстом (&lt; 50 символов).</p></div>
      <div className='card'><h3>Последние проекты</h3>{projects.slice(0, 5).map(p => <div key={p.id} className='sub'>{p.project_name} <ArrowRight size={12} /></div>)}</div>
      <div className='card'><h3>Последние изменения</h3><p className='sub'><Activity size={14} /> Изменения доступны в карточках проектов.</p><p className='sub'><BarChart3 size={14} /> Следите за динамикой заполненности.</p></div>
    </div>
  </div>
}
