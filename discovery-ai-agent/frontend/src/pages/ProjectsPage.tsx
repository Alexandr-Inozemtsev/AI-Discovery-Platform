import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import { Project } from '../types/discovery'

export default function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([])
  const [name, setName] = useState('')
  const [message, setMessage] = useState('')

  const load = async () => {
    try { setProjects(await api<Project[]>('/projects')); setMessage('') }
    catch { setMessage('Backend недоступен. Проверьте, что FastAPI запущен на http://localhost:8000') }
  }
  useEffect(() => { load() }, [])

  const create = async () => {
    if (!name.trim()) return
    try {
      await api<Project>('/projects', { method: 'POST', body: JSON.stringify({ project_name: name }) })
      setName(''); setMessage('Проект успешно создан'); load()
    } catch {
      setMessage('Backend недоступен. Проверьте, что FastAPI запущен на http://localhost:8000')
    }
  }

  return <div>
    <h1>Проекты Discovery</h1>
    <div className='card' style={{ marginBottom: 16 }}>
      <h3>Создать проект</h3>
      <div style={{ display: 'flex', gap: 8 }}>
        <input className='input' value={name} onChange={e => setName(e.target.value)} placeholder='Название проекта' />
        <button className='btn primary' onClick={create}>Создать проект</button>
      </div>
    </div>
    {message && <p className={`message ${message.includes('успешно') ? 'success' : 'error'}`}>{message}</p>}
    <div className='grid'>
      {projects.map(p => <div key={p.id} className='card'>
        <h3 style={{ marginTop: 0 }}>{p.project_name}</h3>
        <p>Статус: <span className='badge'>{p.status}</span></p>
        <p>Этап: {p.current_stage}</p>
        <p>Обновлён: {new Date((p as any).updated_at || Date.now()).toLocaleString('ru-RU')}</p>
        <Link className='btn primary' to={`/projects/${p.id}`}>Открыть</Link>
      </div>)}
    </div>
  </div>
}
