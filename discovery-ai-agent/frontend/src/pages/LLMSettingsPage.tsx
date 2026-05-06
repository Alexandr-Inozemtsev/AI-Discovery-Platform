import { useEffect, useState } from 'react'
import { api } from '../api/client'

export default function LLMSettingsPage(){
  const [f,setF]=useState<any>({provider:'mock',base_url:'https://openrouter.ai/api/v1',api_key:'',model:'openrouter/free',timeout_seconds:120,temperature:0.2,max_tokens:256});
  const [msg,setMsg]=useState(''); const [testResult,setTestResult]=useState<any>(null)
  useEffect(()=>{api<any>('/settings/llm').then(setF)},[])
  const save=async()=>{try{await api('/settings/llm',{method:'PUT',body:JSON.stringify(f)}); setMsg('Настройки LLM сохранены'); window.dispatchEvent(new Event('llm-updated'))}catch{setMsg('Ошибка сохранения')}}
  const test=async()=>{try{const r=await api<any>('/settings/llm/test',{method:'POST',body:JSON.stringify(f)}); setTestResult(r); setMsg('Проверка выполнена'); window.dispatchEvent(new Event('llm-updated'))}catch(e:any){setMsg('Ошибка: '+e.message)}}
  return <div className='card'><h2>Настройки / LLM настройки</h2><div className='goal-grid'>
    <select className='input' value={f.provider} onChange={e=>setF({...f,provider:e.target.value})}><option value='mock'>Mock</option><option value='openrouter'>OpenRouter</option><option value='corporate'>Corporate</option></select>
    <input className='input' value={f.base_url||''} onChange={e=>setF({...f,base_url:e.target.value})} placeholder='https://openrouter.ai/api/v1' />
    <input className='input' value={f.model||''} onChange={e=>setF({...f,model:e.target.value})} placeholder='openrouter/free' />
    <input className='input' value={f.api_key||''} onChange={e=>setF({...f,api_key:e.target.value})} placeholder='API Key (********4078)' />
    <input className='input' type='number' value={f.max_tokens||256} onChange={e=>setF({...f,max_tokens:Number(e.target.value)})} placeholder='Max tokens' />
    <input className='input' type='number' value={f.timeout_seconds} onChange={e=>setF({...f,timeout_seconds:Number(e.target.value)})} placeholder='Timeout' />
    <input className='input' type='number' step='0.1' value={f.temperature} onChange={e=>setF({...f,temperature:Number(e.target.value)})} placeholder='Temperature' />
  </div><div style={{marginTop:12,display:'flex',gap:8,flexWrap:'wrap'}}><button className='btn primary' onClick={save}>Сохранить настройки</button><button className='btn' onClick={test}>Проверить подключение</button><button className='btn' onClick={()=>setF({...f,provider:'mock'})}>Вернуться к Mock</button></div>
  <div style={{marginTop:10}}>
    <div className='sub'>Provider: {f.provider} · Model: {f.model} · Actual: {f.last_actual_model || '—'} · Status: {f.last_connection_status || '—'} · Latency: {f.last_latency_ms || '—'} ms · key_tail: {f.key_tail || 'none'}</div>
    {f.last_error && <div className='sub'>Последняя ошибка: {f.last_error}</div>}
    {Array.isArray(f.error_history) && f.error_history.length>0 && <div><b>История ошибок:</b>{f.error_history.map((e:any,i:number)=><div className='sub' key={i}>{e.time}: {e.error}</div>)}</div>}
    {testResult && <pre style={{whiteSpace:'pre-wrap'}}>{JSON.stringify(testResult,null,2)}</pre>}
    {msg && <p>{msg}</p>}
  </div></div>
}
