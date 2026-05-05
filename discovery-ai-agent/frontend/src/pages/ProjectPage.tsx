import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { api } from '../api/client'
import { ArtifactType, Project } from '../types/discovery'

const tabs: {label: string; type: ArtifactType; generationType?: ArtifactType}[] = [
  { label: 'Контекст', type: 'CONTEXT' },
  { label: 'Проблема', type: 'PROBLEM', generationType: 'PROBLEM' },
  { label: 'Цель', type: 'GOAL', generationType: 'GOAL' },
  { label: 'Бизнес-эффект', type: 'BUSINESS_EFFECT', generationType: 'BUSINESS_EFFECT' },
  { label: 'AS IS', type: 'AS_IS' },
  { label: 'TO BE', type: 'TO_BE' },
  { label: 'Use Cases', type: 'USE_CASES', generationType: 'USE_CASES' },
  { label: 'Требования', type: 'FUNCTIONAL_REQUIREMENTS', generationType: 'FUNCTIONAL_REQUIREMENTS' },
  { label: 'Риски', type: 'RISKS' },
  { label: 'Финальный БТ', type: 'FINAL_BT', generationType: 'FINAL_BT' }
]

export default function ProjectPage() {
  const { projectId } = useParams()
  const [project, setProject] = useState<Project | null>(null)
  const [active, setActive] = useState<ArtifactType>('CONTEXT')
  const [content, setContent] = useState('')
  const [version, setVersion] = useState<number | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  const currentTab = tabs.find(t => t.type === active)
  const canGenerate = Boolean(currentTab?.generationType)

  const loadProject = async () => setProject(await api<Project>(`/projects/${projectId}`))
  const loadArtifact = async (type: ArtifactType) => {
    try { const a = await api<any>(`/projects/${projectId}/artifacts/${type}`); setContent(a.content); setVersion(a.version) }
    catch { setContent(''); setVersion(null) }
  }

  useEffect(() => { loadProject() }, [projectId])
  useEffect(() => { loadArtifact(active) }, [active, projectId])

  const saveProject = async () => {
    try {
      setError('')
      await api(`/projects/${projectId}`, { method: 'PATCH', body: JSON.stringify({ project_name: project?.project_name, business_domain: project?.business_domain, jira_epic_url: project?.jira_epic_url }) })
      loadProject()
    } catch {
      setError('Не удалось сохранить проект. Проверьте доступность backend.')
    }
  }

  const saveArtifact = async () => {
    try {
      setError('')
      const a = await api<any>(`/projects/${projectId}/artifacts/${active}`, { method: 'PUT', body: JSON.stringify({ content }) })
      setVersion(a.version)
    } catch {
      setError('Не удалось сохранить артефакт. Повторите попытку.')
    }
  }

  const generateArtifact = async () => {
    if (!currentTab?.generationType) return
    try {
      setBusy(true); setError('')
      const a = await api<any>(`/projects/${projectId}/generate/${currentTab.generationType}`, { method: 'POST' })
      setContent(a.content)
      setVersion(a.version)
    } catch {
      setError('Ошибка генерации. Для этой вкладки генерация может быть недоступна.')
    } finally { setBusy(false) }
  }

  const validateProject = async () => {
    try {
      setBusy(true); setError('')
      await api<any>(`/projects/${projectId}/validate`, { method: 'POST' })
      setError('Проверка завершена. Отчёт сохранён в VALIDATION_REPORT.')
    } catch {
      setError('Не удалось выполнить проверку проекта.')
    } finally { setBusy(false) }
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
      <button disabled={!canGenerate || busy} onClick={generateArtifact} style={{ marginLeft: 8 }}>{busy ? 'Генерация...' : 'Сгенерировать'}</button>
      <button disabled={busy} onClick={validateProject} style={{ marginLeft: 8 }}>Проверить</button>
      <button disabled style={{ marginLeft: 8 }}>Сформировать БТ</button>
      <span style={{ marginLeft: 12 }}>Версия: {version ?? '—'}</span>
    </div>
    {error && <p style={{ color: error.startsWith('Проверка завершена') ? 'green' : 'crimson' }}>{error}</p>}
  </div>
}
