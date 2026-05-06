import { Route, Routes } from 'react-router-dom'
import LLMSettingsPage from './LLMSettingsPage'

export default function SettingsPage() {
  return <Routes>
    <Route path='llm' element={<LLMSettingsPage />} />
    <Route path='*' element={<LLMSettingsPage />} />
  </Routes>
}
