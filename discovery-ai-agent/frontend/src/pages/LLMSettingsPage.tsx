import { useEffect, useMemo, useState } from 'react'
import { api } from '../api/client'
import Card from '../ui/components/Card'
import Button from '../ui/components/Button'
import Input from '../ui/components/Input'
import PageContainer from '../ui/components/PageContainer'
import StatusIndicator from '../ui/components/StatusIndicator'

type LLMForm = { provider: string; base_url?: string; api_key?: string; model?: string; timeout_seconds: number; temperature: number; max_tokens?: number; last_connection_status?: string; last_error?: string; last_actual_model?: string }

const toUserError = (e: unknown) => `Не удалось выполнить запрос к backend: ${e instanceof Error ? e.message : 'неизвестная ошибка'}`

export default function LLMSettingsPage() {
  const [f, setF] = useState<LLMForm>({ provider: 'mock', base_url: 'https://openrouter.ai/api/v1', api_key: '', model: 'deepseek/deepseek-chat-v3-0324:free', timeout_seconds: 120, temperature: 0.2, max_tokens: 256 })
  const [msg, setMsg] = useState('')

  useEffect(() => { api<LLMForm>('/settings/llm').then(setF).catch((e) => setMsg(toUserError(e))) }, [])
  const status = useMemo<'connected'|'error'|'mock'|'not_configured'>(() => {
    if (f.provider === 'mock') return 'mock'
    if (!f.base_url || !f.model) return 'not_configured'
    if (f.last_connection_status === 'ok') return 'connected'
    if (f.last_error || f.last_connection_status === 'error') return 'error'
    return 'not_configured'
  }, [f])
  const applyPreset = (preset: 'openrouter' | 'corporate' | 'mock') => {
    if (preset === 'openrouter') setF({ ...f, provider: 'openrouter', base_url: 'https://openrouter.ai/api/v1', model: 'deepseek/deepseek-chat-v3-0324:free' })
    if (preset === 'corporate') setF({ ...f, provider: 'corporate', base_url: '', model: '' })
    if (preset === 'mock') setF({ ...f, provider: 'mock' })
  }
  const save = async () => { try { await api('/settings/llm', { method: 'PUT', body: JSON.stringify(f) }); setMsg('Настройки LLM сохранены') } catch (e) { setMsg(toUserError(e)) } }
  const test = async () => { try { await api('/settings/llm/test', { method: 'POST', body: JSON.stringify(f) }); setMsg('Проверка подключения выполнена') } catch (e) { setMsg(toUserError(e)) } }

  return <PageContainer><Card><h2>LLM настройки</h2><p className='sub'>Provider = поставщик LLM-модели · Base URL = адрес API · Model = имя модели · API Key = ключ доступа · Timeout = время ожидания ответа · Temperature = степень вариативности ответа.</p>
    <div style={{ display: 'flex', gap: 8, margin: '12px 0', flexWrap: 'wrap' }}><Button variant='soft' onClick={() => applyPreset('openrouter')}>Preset OpenRouter</Button><Button variant='soft' onClick={() => applyPreset('corporate')}>Preset Corporate</Button><Button variant='soft' onClick={() => applyPreset('mock')}>Preset Mock</Button></div>
    <div className='goal-grid'>
      <select className='ui-input' value={f.provider} onChange={e => setF({ ...f, provider: e.target.value })}><option value='mock'>Mock</option><option value='openrouter'>OpenRouter</option><option value='corporate'>Corporate</option></select>
      <Input value={f.base_url || ''} onChange={e => setF({ ...f, base_url: e.target.value })} placeholder='https://openrouter.ai/api/v1' />
      <Input value={f.model || ''} onChange={e => setF({ ...f, model: e.target.value })} placeholder='deepseek/deepseek-chat-v3-0324:free' />
      <Input value={f.api_key || ''} onChange={e => setF({ ...f, api_key: e.target.value })} placeholder='API Key' />
      <Input type='number' value={f.timeout_seconds} onChange={e => setF({ ...f, timeout_seconds: Number(e.target.value) })} placeholder='Timeout' />
      <Input type='number' step='0.1' value={f.temperature} onChange={e => setF({ ...f, temperature: Number(e.target.value) })} placeholder='Temperature' />
    </div>
    <div style={{ marginTop: 12, display: 'flex', gap: 8, flexWrap: 'wrap' }}><Button variant='primary' onClick={save}>Сохранить настройки</Button><Button onClick={test}>Проверить подключение</Button></div>
  </Card>
  <Card><h3>Статус подключения</h3><StatusIndicator status={status} /><p className='sub' style={{ marginTop: 8 }}>Провайдер: {f.provider} · Модель: {f.model || '—'} · Фактическая модель: {f.last_actual_model || '—'}</p>{f.last_error ? <p className='sub'>Последняя ошибка: {f.last_error}</p> : null}{msg ? <p style={{ marginTop: 8 }}>{msg}</p> : null}</Card>
  </PageContainer>
}
