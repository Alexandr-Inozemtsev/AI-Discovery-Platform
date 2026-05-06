import { useEffect, useMemo, useState } from 'react'
import { Bell, BookCheck, CircleHelp, FileDown, FolderKanban, Gauge, Goal, House, LayoutList, Settings, Target, TriangleAlert } from 'lucide-react'
import { NavLink, Route, Routes } from 'react-router-dom'
import './index.css'
import './App.css'
import ProjectsPage from './pages/ProjectsPage'
import ProjectPage from './pages/ProjectPage'

const workspace = [
  ['CONTEXT', 'Контекст', LayoutList], ['PROBLEM', 'Проблема', TriangleAlert], ['GOAL', 'Цель', Target], ['BUSINESS_EFFECT', 'Бизнес-эффект', Gauge],
  ['AS_IS', 'AS IS', LayoutList], ['TO_BE', 'TO BE', LayoutList], ['USE_CASES', 'Use Cases', FolderKanban], ['FUNCTIONAL_REQUIREMENTS', 'Требования', BookCheck], ['RISKS', 'Риски', TriangleAlert], ['FINAL_BT', 'Финальный БТ', Goal]
]

export default function App() {
  const [ok, setOk] = useState(false)
  useEffect(() => { fetch('http://localhost:8000/health').then(r => setOk(r.ok)).catch(() => setOk(false)) }, [])
  const route = useMemo(() => window.location.pathname, [])

  return <div className='app-shell'>
    <aside className='sidebar'>
      <div className='logo'>AI Discovery Platform</div>
      <NavLink to='/' className={({isActive})=>`nav-item ${isActive?'active':''}`}><House size={16}/>Главная</NavLink>
      <NavLink to='/' className='nav-item'><FolderKanban size={16}/>Проекты</NavLink>
      <div className='section-title'>Discovery Workspace</div>
      {workspace.map(([key,label,Icon]) => <div key={key} className={`nav-item ${route.includes('/projects/') ? 'active':''}`}><Icon size={16}/>{label}</div>)}
      <div className='section-title'>Инструменты</div>
      <div className='nav-item'><BookCheck size={16}/>Проверка полноты</div>
      <div className='nav-item'><FileDown size={16}/>Экспорт БТ (DOCX)</div>
      <div style={{marginTop:'auto'}}>
        <div className='nav-item'><Settings size={16}/>Настройки</div>
        <div className='nav-item'>⇤ Свернуть меню</div>
      </div>
    </aside>

    <main className='main'>
      <div className='topbar'>
        <div><span className='status-ok' style={{background:ok?'var(--success)':'#ef4444'}}/>Backend: {ok?'подключен':'недоступен'}</div>
        <div style={{display:'flex',alignItems:'center',gap:12}}><CircleHelp size={18}/><Bell size={18}/><div style={{width:30,height:30,borderRadius:999,background:'#dbeafe',display:'grid',placeItems:'center',fontWeight:700}}>A</div><strong>Александр</strong></div>
      </div>
      <div className='content'>
        <Routes>
          <Route path='/' element={<ProjectsPage />} />
          <Route path='/projects/:projectId' element={<ProjectPage />} />
        </Routes>
      </div>
    </main>
  </div>
}
