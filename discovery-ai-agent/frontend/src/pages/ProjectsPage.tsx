import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import { Project } from '../types/discovery'

export default function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([])
  const [name, setName] = useState('')

  const load = () => api<Project[]>('/projects').then(setProjects)
  useEffect(() => { load() }, [])

  const create = async () => {
    if (!name.trim()) return
    // Русский комментарий: создание проекта минимальным payload.
    await api<Project>('/projects', { method: 'POST', body: JSON.stringify({ project_name: name }) })
    setName(''); load()
  }

  return <div style={{ padding: 24 }}>
    <h1>Discovery Projects</h1>
    <div><input value={name} onChange={e => setName(e.target.value)} placeholder='Название проекта' /> <button onClick={create}>Создать проект</button></div>
    <table border={1} cellPadding={8} style={{ marginTop: 12, width: '100%' }}><thead><tr><th>Название</th><th>Статус</th><th>Этап</th><th></th></tr></thead><tbody>
      {projects.map(p => <tr key={p.id}><td>{p.project_name}</td><td>{p.status}</td><td>{p.current_stage}</td><td><Link to={`/projects/${p.id}`}>Открыть</Link></td></tr>)}
    </tbody></table>
  </div>
}
