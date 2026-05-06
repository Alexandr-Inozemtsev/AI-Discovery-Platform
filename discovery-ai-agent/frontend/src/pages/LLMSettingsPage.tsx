import { useEffect, useState } from 'react'
import { api } from '../api/client'

export default function LLMSettingsPage(){
  const [f,setF]=useState<any>({provider:'mock',base_url:'',api_key:'',model:'',timeout_seconds:60,temperature:0.2}); const [msg,setMsg]=useState('')
  useEffect(()=>{api<any>('/settings/llm').then(setF)},[])
  const save=async()=>{try{await api('/settings/llm',{method:'PUT',body:JSON.stringify(f)}); setMsg('Сохранено')}catch(e:any){setMsg('Ошибка сохранения')}}
  const test=async()=>{try{const r=await api<any>('/settings/llm/test',{method:'POST'}); setMsg('Успешно: '+r.message)}catch(e:any){setMsg('Ошибка: '+e.message)}}
  return <div className='card'><h2>LLM настройки</h2><div className='goal-grid'>
    <select className='input' value={f.provider} onChange={e=>setF({...f,provider:e.target.value})}><option value='mock'>Mock</option><option value='openrouter'>OpenRouter</option><option value='corporate'>Corporate</option></select>
    <input className='input' value={f.base_url||''} onChange={e=>setF({...f,base_url:e.target.value})} placeholder={f.provider==='corporate'?'https://llm.company.ru/v1':'https://openrouter.ai/api/v1'} />
    <input className='input' value={f.model||''} onChange={e=>setF({...f,model:e.target.value})} placeholder={f.provider==='corporate'?'company-model':'deepseek/deepseek-chat-v3-0324:free'} />
    <input className='input' value={f.api_key||''} onChange={e=>setF({...f,api_key:e.target.value})} placeholder='API Key' />
    <input className='input' type='number' value={f.timeout_seconds} onChange={e=>setF({...f,timeout_seconds:Number(e.target.value)})} placeholder='Timeout' />
    <input className='input' type='number' step='0.1' value={f.temperature} onChange={e=>setF({...f,temperature:Number(e.target.value)})} placeholder='Temperature' />
  </div><div style={{marginTop:12,display:'flex',gap:8}}><button className='btn primary' onClick={save}>Сохранить настройки</button><button className='btn' onClick={test}>Проверить подключение</button><button className='btn' onClick={()=>setF({...f,provider:'mock'})}>Вернуться к Mock</button></div>{msg && <p>{msg}</p>}</div>
}
