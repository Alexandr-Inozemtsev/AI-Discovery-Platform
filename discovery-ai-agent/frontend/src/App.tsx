import { useEffect, useMemo, useState } from 'react'
import { Bell, BookCheck, CircleHelp, FileDown, FolderKanban, Gauge, Goal, House, LayoutList, Settings, Target, TriangleAlert } from 'lucide-react'
import { NavLink, Route, Routes, useLocation, useNavigate, useSearchParams } from 'react-router-dom'
import './index.css'
import './App.css'
import ProjectsPage from './pages/ProjectsPage'
import HomePage from './pages/HomePage'
import ProjectPage from './pages/ProjectPage'
import SettingsPage from './pages/SettingsPage'
import { api } from './api/client'
import ErrorBoundary from './components/ErrorBoundary'
import AppShell from './ui/components/AppShell'
import Sidebar from './ui/components/Sidebar'
import TopHeader from './ui/components/TopHeader'
import Badge from './ui/components/Badge'
import Button from './ui/components/Button'

const workspace:[string,string,any][] = [
  ['CONTEXT', 'Контекст', LayoutList], ['PROBLEM', 'Проблема', TriangleAlert], ['GOAL', 'Цель', Target], ['BUSINESS_EFFECT', 'Бизнес-эффект', Gauge],
  ['AS_IS', 'AS IS', LayoutList], ['TO_BE', 'TO BE', LayoutList], ['USE_CASES', 'Use Cases', FolderKanban], ['FUNCTIONAL_REQUIREMENTS', 'Требования', BookCheck], ['RISKS', 'Риски', TriangleAlert], ['FINAL_BT', 'Финальный БТ', Goal]
]

export default function App() {
  const [ok, setOk] = useState(false)
  const [msg, setMsg] = useState('')
  const [llm, setLlm] = useState<any>({provider:'mock',model:'-'})
  const location = useLocation(); const navigate = useNavigate(); const [sp] = useSearchParams()
  const currentProjectId = useMemo(() => (location.pathname.match(/^\/projects\/([^/]+)/)?.[1] || localStorage.getItem('lastOpenedProjectId') || ''), [location.pathname])
  useEffect(() => {const refresh = () => api<any>('/settings/llm').then(setLlm).catch(()=>{}); fetch('http://localhost:8000/health').then(r => setOk(r.ok)).catch(() => setOk(false)); refresh()}, [])
  const goStage = (stage: string) => {const pid = currentProjectId || localStorage.getItem('lastOpenedProjectId'); if (!pid) return setMsg('Сначала создайте или откройте проект'); setMsg(''); navigate(`/projects/${pid}?stage=${stage}`)}

  return <AppShell
    sidebar={<Sidebar><div className='logo'>✕ AI Discovery Platform</div><NavLink to='/' className={({isActive})=>`nav-item ${isActive?'active':''}`}><House size={16}/>Главная</NavLink><NavLink to='/projects' className={({isActive})=>`nav-item ${isActive?'active':''}`}><FolderKanban size={16}/>Проекты</NavLink><div className='section-title'>DISCOVERY WORKSPACE</div>{workspace.map(([key,label,Icon]) => <Button key={key} size='sm' variant='ghost' onClick={()=>goStage(key)} className={`nav-item ${sp.get('stage')===key ? 'active':''}`}><Icon size={16}/>{label}</Button>)}<div className='section-title'>ИНСТРУМЕНТЫ</div><div className='nav-item'><BookCheck size={16}/>Проверка полноты</div><div className='nav-item'><FileDown size={16}/>Экспорт БТ (DOCX)</div><div className='sidebar-bottom'><NavLink to='/settings/llm' className={({isActive})=>`nav-item ${isActive?'active':''}`}><Settings size={16}/>Настройки</NavLink></div></Sidebar>}
    header={<TopHeader left={<div className='ui-top-meta'><h2 className='ui-top-title'>Автопролонгация ИБС</h2><Badge text='В работе' variant='ready'/><span className='sub'>Версия: 33</span><span className='sub'>Обновлено: 06.05.2026, 09:15:12</span></div>} right={<div className='ui-top-meta'><span className='sub'><span className={`status-dot ${ok?'ok':'bad'}`}/> Backend: {ok?'подключен':'недоступен'}</span><CircleHelp size={18}/><Bell size={18}/><div className='ui-avatar'>A</div><strong>Александр</strong></div>} />}
  >
    {msg && <div className='ui-card app-msg'>{msg}</div>}
    <Routes>
      <Route path='/' element={<HomePage />} />
      <Route path='/projects' element={<ProjectsPage />} />
      <Route path='/projects/:projectId' element={<ErrorBoundary fallbackTitle='Ошибка экрана проекта'><ProjectPage /></ErrorBoundary>} />
      <Route path='/settings/*' element={<SettingsPage />} />
    </Routes>
  </AppShell>
}
