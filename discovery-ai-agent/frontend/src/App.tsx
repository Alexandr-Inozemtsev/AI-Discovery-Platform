import { useEffect, useMemo, useState } from 'react'
import { Bell, BookCheck, CircleHelp, FileDown, FolderKanban, Gauge, Goal, House, LayoutList, Settings, Target, TriangleAlert } from 'lucide-react'
import { NavLink, Route, Routes, useLocation, useNavigate, useSearchParams } from 'react-router-dom'
import './index.css'
import './App.css'
import ProjectsPage from './pages/ProjectsPage'
import ProjectPage from './pages/ProjectPage'

const workspace:[string,string,any][] = [
  ['CONTEXT', 'Контекст', LayoutList], ['PROBLEM', 'Проблема', TriangleAlert], ['GOAL', 'Цель', Target], ['BUSINESS_EFFECT', 'Бизнес-эффект', Gauge],
  ['AS_IS', 'AS IS', LayoutList], ['TO_BE', 'TO BE', LayoutList], ['USE_CASES', 'Use Cases', FolderKanban], ['FUNCTIONAL_REQUIREMENTS', 'Требования', BookCheck], ['RISKS', 'Риски', TriangleAlert], ['FINAL_BT', 'Финальный БТ', Goal]
]

export default function App() {
  const [ok, setOk] = useState(false)
  const [msg, setMsg] = useState('')
  const location = useLocation(); const navigate = useNavigate(); const [sp] = useSearchParams()
  const currentProjectId = useMemo(() => {
    const m = location.pathname.match(/^\/projects\/([^/]+)/)
    return m?.[1] || localStorage.getItem('lastOpenedProjectId') || ''
  }, [location.pathname])

  useEffect(() => { fetch('http://localhost:8000/health').then(r => setOk(r.ok)).catch(() => setOk(false)) }, [])

  const goStage = (stage: string) => {
    const pid = currentProjectId || localStorage.getItem('lastOpenedProjectId')
    if (!pid) return setMsg('Сначала создайте или откройте проект')
    setMsg('')
    navigate(`/projects/${pid}?stage=${stage}`)
  }

  return <div className='app-shell'>
    <aside className='sidebar'>
      <div className='logo'>AI Discovery Platform</div>
      <NavLink to='/' className={({isActive})=>`nav-item ${isActive?'active':''}`}><House size={16}/>Главная</NavLink>
      <NavLink to='/' className='nav-item'><FolderKanban size={16}/>Проекты</NavLink>
      <div className='card' style={{background:'rgba(255,255,255,.06)',borderColor:'rgba(148,163,184,.25)',color:'#cbd5e1',padding:'10px 12px'}}>
        <div className='sub' style={{color:'#94a3b8'}}>Текущий проект</div>
        <div style={{fontWeight:700,color:'#fff'}}>{currentProjectId || 'Не выбран'}</div>
        <div className='sub' style={{color:'#94a3b8'}}>Прогресс: 0%</div>
      </div>
      <div className='section-title'>Discovery Workspace</div>
      {workspace.map(([key,label,Icon]) => <button key={key} onClick={()=>goStage(key)} className={`nav-item ${sp.get('stage')===key ? 'active':''}`}><Icon size={16}/>{label}</button>)}
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
      {msg && <div className='card' style={{marginBottom:10,color:'#b45309'}}>{msg}</div>}
      <div className='content'>
        <Routes>
          <Route path='/' element={<ProjectsPage />} />
          <Route path='/projects/:projectId' element={<ProjectPage />} />
        </Routes>
      </div>
    </main>
  </div>
}
