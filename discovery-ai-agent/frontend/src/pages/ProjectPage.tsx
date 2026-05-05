import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { api } from '../api/client'
import { ArtifactType, Project } from '../types/discovery'

const tabs: {label: string; type: ArtifactType}[] = [
  { label: 'Контекст', type: 'CONTEXT' }, { label: 'Проблема', type: 'PROBLEM' }, { label: 'Цель', type: 'GOAL' },
  { label: 'Бизнес-эффект', type: 'BUSINESS_EFFECT' }, { label: 'AS IS', type: 'AS_IS' }, { label: 'TO BE', type: 'TO_BE' },
  { label: 'Use Cases', type: 'USE_CASES' }, { label: 'Требования', type: 'FUNCTIONAL_REQUIREMENTS' }, { label: 'Риски', type: 'RISKS' }, { label: 'Финальный БТ', type: 'FINAL_BT' }
]

export default function ProjectPage() {
  const { projectId } = useParams()
  const [project, setProject] = useState<Project | null>(null)
  const [active, setActive] = useState<ArtifactType>('CONTEXT')
  const [content, setContent] = useState('')
  const [version, setVersion] = useState<number | null>(null)

  const loadProject = async () => setProject(await api<Project>(`/projects/${projectId}`))
  const loadArtifact = async (type: ArtifactType) => {
    try { const a = await api<any>(`/projects/${projectId}/artifacts/${type}`); setContent(a.content); setVersion(a.version) }
    catch { setContent(''); setVersion(null) }
  }
  useEffect(() => { loadProject() }, [projectId])
  useEffect(() => { loadArtifact(active) }, [active, projectId])

  const saveProject = async () => {
    await api(`/projects/${projectId}`, { method: 'PATCH', body: JSON.stringify({ project_name: project?.project_name, business_domain: project?.business_domain, jira_epic_url: project?.jira_epic_url }) })
    loadProject()
  }
  const saveArtifact = async () => {
    const a = await api<any>(`/projects/${projectId}/artifacts/${active}`, { method: 'PUT', body: JSON.stringify({ content }) })
    setVersion(a.version)
  }

  if (!project) return <div style={{ padding: 24 }}>Loading...</div>
  return <div style={{ padding: 24 }}>
    <h2>{project.project_name}</h2>
    <div style={{ border: '1px solid #ccc', padding: 12, marginBottom: 16 }}>
      <input value={project.project_name} onChange={e => setProject({ ...project, project_name: e.target.value })} placeholder='Название проекта' />
      <input value={project.business_domain || ''} onChange={e => setProject({ ...project, business_domain: e.target.value })} placeholder='Бизнес-домен' />
      <input value={project.jira_epic_url || ''} onChange={e => setProject({ ...project, jira_epic_url: e.target.value })} placeholder='Jira Epic URL' />
      <button onClick={saveProject}>Сохранить проект</button>
      <p>Status: {project.status} | Stage: {project.current_stage}</p>
    </div>
    <div>{tabs.map(t => <button key={t.type} onClick={() => setActive(t.type)} style={{ marginRight: 8 }}>{t.label}</button>)}</div>
    <textarea value={content} onChange={e => setContent(e.target.value)} style={{ width: '100%', minHeight: 220, marginTop: 12 }} />
    <div style={{ marginTop: 8 }}>
      <button onClick={saveArtifact}>Сохранить</button>
      <button disabled style={{ marginLeft: 8 }}>Сгенерировать</button>
      <button disabled style={{ marginLeft: 8 }}>Проверить</button>
      <button disabled style={{ marginLeft: 8 }}>Сформировать БТ</button>
      <span style={{ marginLeft: 12 }}>Версия: {version ?? '—'}</span>
    </div>
  </div>
}
