import { Link, Route, Routes } from 'react-router-dom'
import './index.css'
import './App.css'
import ProjectsPage from './pages/ProjectsPage'
import ProjectPage from './pages/ProjectPage'

export default function App() {
  return (
    <>
      <header className='topbar'>
        <div className='topbar-inner'>
          <div>
            <div className='title'>AI Discovery Platform</div>
            <div className='subtitle'>Рабочее пространство для подготовки Discovery и БТ</div>
          </div>
          <Link to='/' className='btn'>На главную</Link>
        </div>
      </header>
      <main className='container'>
        <Routes>
          <Route path='/' element={<ProjectsPage />} />
          <Route path='/projects/:projectId' element={<ProjectPage />} />
        </Routes>
      </main>
    </>
  )
}
