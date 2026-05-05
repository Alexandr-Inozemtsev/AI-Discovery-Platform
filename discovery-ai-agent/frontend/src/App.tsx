import { useEffect, useState } from 'react'
import { Link, Route, Routes } from 'react-router-dom'
import ProjectsPage from './pages/ProjectsPage'
import ProjectPage from './pages/ProjectPage'

export default function App() {
  const [ok, setOk] = useState(false)
  useEffect(() => { fetch('http://localhost:8000/health').then(r => setOk(r.ok)).catch(() => setOk(false)) }, [])
  return <>
    <header className='topbar'><div className='topbar-inner'><div><div className='brand'>AI Discovery Platform</div><div className='sub'>Рабочее пространство владельца продукта для Discovery и подготовки БТ</div></div><div><span className='status-dot' style={{background:ok?'#22c55e':'#ef4444'}}></span>{ok?'Backend подключён':'Backend недоступен'} <Link to='/' className='btn' style={{marginLeft:10}}>На главную</Link></div></div></header>
    <main className='container'><Routes><Route path='/' element={<ProjectsPage />} /><Route path='/projects/:projectId' element={<ProjectPage />} /></Routes></main>
  </>
}
