import { useEffect, useMemo, useState } from 'react'
import { ApiError, api } from '../api/client'
import Card from '../ui/components/Card'
import Button from '../ui/components/Button'
import Input from '../ui/components/Input'
import PageContainer from '../ui/components/PageContainer'
import StatusIndicator from '../ui/components/StatusIndicator'

type LLMForm = { provider: string; base_url?: string; api_key?: string; model?: string; timeout_seconds: number; temperature: number; last_connection_status?: string; last_error?: string; last_actual_model?: string; key_tail?: string; last_latency_ms?: number; human_message?: string }

export default function LLMSettingsPage() {
  const [f, setF] = useState<LLMForm>({ provider: 'mock', base_url: 'https://openrouter.ai/api/v1', api_key: '', model: 'deepseek/deepseek-chat-v3-0324:free', timeout_seconds: 120, temperature: 0.2 })
  const [msg, setMsg] = useState('')
  const load = async () => { try { setF(await api<LLMForm>('/settings/llm')) } catch (e: any) { setMsg(e?.message || 'Ошибка загрузки') } }
  useEffect(() => { load() }, [])

  const status = useMemo<any>(() => {
    const map: Record<string, any> = { connected: 'connected', mock: 'mock', not_configured: 'not_configured', unauthorized: 'error', model_not_found: 'warning', timeout: 'warning', backend_error: 'error', error: 'error' }
    return map[f.last_connection_status || 'not_configured'] || 'not_configured'
  }, [f.last_connection_status])

  const applyPreset = (preset: 'openrouter' | 'corporate' | 'mock') => {
    if (preset === 'openrouter') setF({ ...f, provider: 'openrouter', base_url: 'https://openrouter.ai/api/v1', model: 'deepseek/deepseek-chat-v3-0324:free' })
    if (preset === 'corporate') setF({ ...f, provider: 'corporate', base_url: '', model: '' })
    if (preset === 'mock') setF({ ...f, provider: 'mock' })
  }

  const save = async () => { try { await api('/settings/llm', { method: 'PUT', body: JSON.stringify(f) }); await load(); setMsg('Настройки сохранены') } catch (e) { setMsg(e instanceof ApiError ? e.message : 'Ошибка сохранения') } }
  const test = async () => { try { await api('/settings/llm/test', { method: 'POST', body: JSON.stringify(f) }); await load(); setMsg('Проверка завершена') } catch (e) { setMsg(e instanceof ApiError ? e.message : 'Ошибка проверки') } }

  return <PageContainer><Card><h2>LLM настройки</h2><p className='sub'>Provider — поставщик LLM-модели. Base URL — адрес API совместимого с OpenAI. Model — техническое имя модели. API Key — секретный ключ доступа. Timeout — сколько секунд ждать ответ. Temperature — насколько вариативным будет ответ.</p>
    <div className='ui-actions'><Button variant='soft' onClick={() => applyPreset('openrouter')}>Preset OpenRouter</Button><Button variant='soft' onClick={() => applyPreset('corporate')}>Preset Corporate</Button><Button variant='soft' onClick={() => applyPreset('mock')}>Preset Mock</Button></div>
    <div className='goal-grid'>
      <select className='ui-input' value={f.provider} onChange={e => setF({ ...f, provider: e.target.value })}><option value='mock'>Mock</option><option value='openrouter'>OpenRouter</option><option value='corporate'>Corporate</option></select>
      <Input value={f.base_url || ''} onChange={e => setF({ ...f, base_url: e.target.value })} placeholder='https://openrouter.ai/api/v1' />
      <Input value={f.model || ''} onChange={e => setF({ ...f, model: e.target.value })} placeholder='deepseek/deepseek-chat-v3-0324:free' />
      <Input value={f.api_key || ''} onChange={e => setF({ ...f, api_key: e.target.value })} placeholder='API Key' />
      <Input type='number' value={f.timeout_seconds} onChange={e => setF({ ...f, timeout_seconds: Number(e.target.value) })} placeholder='Timeout' />
      <Input type='number' step='0.1' value={f.temperature} onChange={e => setF({ ...f, temperature: Number(e.target.value) })} placeholder='Temperature' />
    </div><div className='ui-actions'><Button variant='primary' onClick={save}>Сохранить</Button><Button onClick={test}>Проверить подключение</Button></div></Card>
  <Card><h3>Статус подключения</h3><StatusIndicator status={status} /><p className='sub status-meta'>Provider: {f.provider} · Base URL: {f.base_url || '—'} · Model: {f.model || '—'} · Actual: {f.last_actual_model || '—'} · key_tail: {f.key_tail || '—'} · latency: {f.last_latency_ms || 0} ms</p><p className='sub'>{f.human_message || '—'}</p>{f.last_error ? <p className='sub'>Ошибка: {f.last_error}</p> : null}{msg ? <p className='status-meta'>{msg}</p> : null}</Card>
  </PageContainer>
}
