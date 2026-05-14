import { ArrowRight, ClipboardCopy, ListChecks, RefreshCcw } from 'lucide-react'
import { useState } from 'react'
import Button from '../../../ui/components/Button'
import Card from '../../../ui/components/Card'

export default function AIAssistantCard({onGoProblem,onRefresh,allMetadataOnly,readiness,missingInformation,problemHandoff}:{onGoProblem:()=>void;onRefresh:()=>void;allMetadataOnly?:boolean;readiness?:any;missingInformation:string[];problemHandoff:any}){
  const [showMissing,setShowMissing]=useState(false)
  const [copied,setCopied]=useState(false)
  const status=readiness?.status||'blocked'
  const label=status==='ready'?'Готов к Problem':status==='warning'?'Можно перейти с предупреждением':'Низкое качество контекста'
  const badge=status==='ready'?'ready':status==='warning'?'warning':'error'
  const summary=problemHandoff?.context_summary||readiness?.summary||''
  const copySummary=async()=>{
    const text=summary||'Summary для Problem-agent пока не сформирован. Обновите контекст.'
    await navigator.clipboard?.writeText(text)
    setCopied(true)
    setTimeout(()=>setCopied(false),1500)
  }
  const missing=[...(missingInformation||[]),...((readiness?.blocking_reasons||[]) as string[]),...((readiness?.warnings||[]) as string[])].filter(Boolean)
  return <Card title='Действия с контекстом'>
    <div className='assistant-stack'>
      <div className='assistant-card'>
        <div className='assistant-card__title'>Готовность</div>
        <span className={`ui-badge ${badge}`}>{label} · {readiness?.score??0}%</span>
        <p>{allMetadataOnly?'Файлы добавлены, но текст документов не извлечён. Такой контекст не считается использованным источником.':(readiness?.summary||'Готовность появится после обновления контекста.')}</p>
      </div>
      <div className='context-action-grid'>
        <Button size='sm' variant='primary' onClick={onRefresh}><RefreshCcw size={14}/>Обновить контекст</Button>
        <Button size='sm' variant='secondary' onClick={()=>setShowMissing(v=>!v)}><ListChecks size={14}/>Показать, чего не хватает</Button>
        <Button size='sm' variant='secondary' onClick={onGoProblem}><ArrowRight size={14}/>Перейти к проблеме</Button>
        <Button size='sm' variant='soft' onClick={copySummary}><ClipboardCopy size={14}/>{copied?'Скопировано':'Скопировать summary'}</Button>
      </div>
      {showMissing&&<div className='hint-card'><b>Недостающая информация</b>{missing.length?<ul>{missing.slice(0,10).map((m,i)=><li key={i}>{m}</li>)}</ul>:<p className='sub'>Критичных пробелов не найдено.</p>}</div>}
      {summary&&<div className='assistant-card'><div className='assistant-card__title'>Summary для Problem-agent</div><p>{summary}</p></div>}
    </div>
  </Card>
}
