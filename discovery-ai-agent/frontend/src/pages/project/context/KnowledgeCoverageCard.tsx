import { AlertTriangle, CheckCircle2, XCircle } from 'lucide-react'
import Card from '../../../ui/components/Card'

export default function KnowledgeCoverageCard({coverage,readiness,sourceTrace}:{coverage:any;readiness?:any;sourceTrace:any[]}){
  const docs=sourceTrace.filter((s:any)=>s.source_type==='document')
  const withText=docs.filter((d:any)=>d.used&&d.content_level!=='metadata_only').length
  const docsStatus=docs.length===0?'Нет данных':withText===0?'Только метаданные':withText<docs.length?'Частично':'OK'
  const notEnoughText=docs.length>0&&withText===0
  const rows=[
    ['Ручной контекст',coverage?.manual_context?'OK':'Нет данных',coverage?.manual_context?'ready':'warning'],
    ['Документы',docsStatus,docsStatus==='OK'?'ready':docsStatus==='Частично'?'warning':'warning'],
    ['Процессы',coverage?.processes?'OK':(notEnoughText?'Недостаточно текста':'Нет данных'),coverage?.processes?'ready':'warning'],
    ['Системы',coverage?.systems?'OK':(notEnoughText?'Недостаточно текста':'Нет данных'),coverage?.systems?'ready':'warning'],
    ['Участники / ответственные',coverage?.roles?'OK':'Нет данных',coverage?.roles?'ready':'warning'],
    ['Интеграции',coverage?.integrations?'OK':(notEnoughText?'Недостаточно текста':'Нет данных'),coverage?.integrations?'ready':'warning'],
    ['Метрики / KPI',coverage?.kpi?'OK':'Нет данных',coverage?.kpi?'ready':'warning'],
    ['BPMN',coverage?.bpmn?'OK':'Нет BPMN',coverage?.bpmn?'ready':'warning'],
    ['SLA',coverage?.sla?'OK':'Нет SLA',coverage?.sla?'ready':'warning'],
    ['Ограничения',coverage?.constraints?'OK':'Не указаны',coverage?.constraints?'ready':'warning']
  ] as const
  const hints=[] as string[]
  if(notEnoughText) hints.push('Замените metadata-only документы на файлы с извлекаемым текстом')
  if(!coverage?.manual_context) hints.push('Заполните ручной бизнес-контекст')
  if(!coverage?.processes) hints.push('Добавьте описание текущего процесса или BPMN')
  if(!coverage?.systems) hints.push('Укажите затронутые системы')
  if(!coverage?.kpi) hints.push('Уточните KPI и целевые метрики')
  if(!coverage?.constraints) hints.push('Добавьте ограничения и допущения')
  const readinessLabel=readiness?.status==='ready'?'Готов':readiness?.status==='warning'?'Можно с предупреждением':readiness?.status==='blocked'?'Заблокирован':'Не рассчитана'
  const readinessClass=readiness?.status==='ready'?'ready':readiness?.status==='blocked'?'error':'warning'
  return <Card title='Покрытие знаний'>
    <div className='readiness-mini'>
      <div><b>Готовность контекста</b><p className='sub'>{readiness?.summary||'Нажмите «Обновить контекст», чтобы рассчитать готовность.'}</p></div>
      <span className={`ui-badge ${readinessClass}`}>{readinessLabel} · {readiness?.score??0}%</span>
    </div>
    <div className='coverage-list'>{rows.map(([l,status,badge])=><div className='coverage-item' key={l}><span className='coverage-left'>{status==='OK'?<CheckCircle2 size={16} className='ok'/>:status.includes('Нет')?<XCircle size={16} className='bad'/>:<AlertTriangle size={16} className='warn'/>}<span className='coverage-label'>{l}</span></span><span className={`coverage-status ui-badge ${badge}`}>{status}</span></div>)}</div>
    {hints.length>0&&<div className='hint-card'><b>Что ещё можно добавить</b><ul>{hints.slice(0,6).map((h,i)=><li key={i}>{h}</li>)}</ul></div>}
  </Card>
}
