import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api } from '../api/client'
import { ArtifactType, Project } from '../types/discovery'

const tabs:{label:string;type:ArtifactType;description:string}[]=[
{label:'Контекст',type:'CONTEXT',description:'Опишите бизнес-контекст и ограничения.'},{label:'Проблема',type:'PROBLEM',description:'Сформулируйте ключевую проблему и её влияние.'},
{label:'Цель',type:'GOAL',description:'Определите цель и ожидаемый результат.'},{label:'Бизнес-эффект',type:'BUSINESS_EFFECT',description:'Зафиксируйте качественные и количественные эффекты.'},
{label:'AS IS',type:'AS_IS',description:'Текущее состояние процесса.'},{label:'TO BE',type:'TO_BE',description:'Целевое состояние после изменений.'},
{label:'Use Cases',type:'USE_CASES',description:'Опишите основные пользовательские сценарии.'},{label:'Требования',type:'FUNCTIONAL_REQUIREMENTS',description:'Соберите функциональные и бизнес-требования.'},
{label:'Риски',type:'RISKS',description:'Перечислите риски и меры митигации.'},{label:'Финальный БТ',type:'FINAL_BT',description:'Соберите финальный черновик БТ.'}]

export default function ProjectPage(){
  const {projectId}=useParams(); const [project,setProject]=useState<Project|null>(null)
  const [active,setActive]=useState<ArtifactType>('CONTEXT'); const [content,setContent]=useState(''); const [version,setVersion]=useState<number|null>(null)
  const [busy,setBusy]=useState(false); const [message,setMessage]=useState(''); const [completion,setCompletion]=useState<any>(null)
  const current=tabs.find(t=>t.type===active)

  const loadProject=async()=>{ try{ setProject(await api<Project>(`/projects/${projectId}`)); setMessage('') } catch{ setMessage('Проект не найден') } }
  const loadCompletion=async()=>{ try{ setCompletion(await api<any>(`/projects/${projectId}/completion`)) } catch{} }
  const loadArtifact=async(type:ArtifactType)=>{ try{const a=await api<any>(`/projects/${projectId}/artifacts/${type}`); setContent(a.content||''); setVersion(a.version)} catch{ setContent(''); setVersion(null) } }
  useEffect(()=>{loadProject(); loadCompletion()},[projectId]); useEffect(()=>{loadArtifact(active)},[active,projectId])

  const saveProject=async()=>{ try{ await api(`/projects/${projectId}`,{method:'PATCH',body:JSON.stringify({project_name:project?.project_name,business_domain:(project as any)?.business_domain,jira_epic_url:(project as any)?.jira_epic_url})}); setMessage('Проект успешно сохранён'); loadProject() } catch { setMessage('Backend недоступен. Проверьте, что FastAPI запущен на http://localhost:8000') } }
  const saveArtifact=async()=>{ try{ const a=await api<any>(`/projects/${projectId}/artifacts/${active}`,{method:'PUT',body:JSON.stringify({content})}); setVersion(a.version); setMessage('Артефакт успешно сохранён'); loadCompletion() } catch{ setMessage('Backend недоступен. Проверьте, что FastAPI запущен на http://localhost:8000') } }
  const generate=async()=>{ try{ setBusy(true); const a=await api<any>(`/projects/${projectId}/generate/${active}`,{method:'POST'}); setContent(a.content); setVersion(a.version); setMessage('Генерация завершена'); loadCompletion()} catch{ setMessage('Ошибка генерации для этого этапа') } finally{ setBusy(false)} }
  const validate=async()=>{ try{ setBusy(true); await api<any>(`/projects/${projectId}/validate`,{method:'POST'}); setMessage('Проверка завершена'); } catch { setMessage('Ошибка проверки') } finally{ setBusy(false)} }

  if(!project) return <div className='card'>Проект не найден</div>
  return <div className='layout'>
    <aside className='card'>
      <h3>Этапы Discovery</h3>
      {tabs.map(t=>{const st=completion?.sections?.find((s:any)=>s.artifact_type===t.type); return <div key={t.type} className={`sidebar-item ${active===t.type?'active':''}`} onClick={()=>setActive(t.type)}><span>{t.label}</span><span style={{color:st?.is_completed?'#16a34a':'#9ca3af'}}>{st?.is_completed?'●':'○'}</span></div>})}
    </aside>
    <section>
      <div className='card' style={{marginBottom:12}}>
        <div className='actions'><Link to='/' className='btn'>← К списку проектов</Link><button className='btn primary' onClick={saveProject}>Сохранить проект</button></div>
        <div className='project-meta' style={{marginTop:10}}>
          <input className='input' value={project.project_name} onChange={e=>setProject({...project,project_name:e.target.value})} placeholder='Название' />
          <input className='input' value={(project as any).business_domain||''} onChange={e=>setProject({...project,business_domain:e.target.value} as any)} placeholder='Бизнес-направление' />
          <input className='input' value={(project as any).jira_epic_url||''} onChange={e=>setProject({...project,jira_epic_url:e.target.value} as any)} placeholder='Ссылка Jira Epic' />
          <div className='card' style={{padding:10}}>Статус: {(project as any).status} · Этап: {(project as any).current_stage}</div>
        </div>
      </div>
      <div className='card'>
        <h2 style={{marginTop:0}}>{current?.label}</h2>
        <p style={{color:'#6b7280'}}>{current?.description}</p>
        <textarea className='textarea' value={content} onChange={e=>setContent(e.target.value)} />
        <div className='actions'>
          <button className='btn primary' onClick={saveArtifact}>Сохранить</button>
          <button className='btn' disabled={busy} onClick={generate}>{busy?'Генерация...':'Сгенерировать'}</button>
          <button className='btn' disabled={busy} onClick={validate}>Проверить</button>
          <span style={{marginLeft:'auto'}}>Версия: {version??'—'}</span>
        </div>
      </div>
      {message && <p className={`message ${message.includes('успеш') || message.includes('завершена') ? 'success' : 'error'}`}>{message}</p>}
    </section>
  </div>
}
