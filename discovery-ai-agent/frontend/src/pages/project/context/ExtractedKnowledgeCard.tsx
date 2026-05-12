import Card from '../../../ui/components/Card'
const groups:[string,string[]][]=[['Процессы',['процессы','processes']],['Системы',['системы','systems']],['Роли',['роли','roles']],['Интеграции',['интеграции','integrations']],['Ключевые сущности',['бизнес_сущности','business_entities']],['Документы',['документы','documents']],['Термины',['термины','terms']]]

export default function ExtractedKnowledgeCard({knowledge}:{knowledge:any}){
  const emptyMajor=groups.every(([,keys])=>keys.filter(k=>!['documents','документы'].includes(k)).flatMap(k=>Array.isArray(knowledge?.[k])?knowledge[k]:[]).length===0)
  const missing=(knowledge?.missing_information||[]).slice(0,5)
  const metadataOnly=(knowledge?.source_trace||[]).length>0 && (knowledge?.source_trace||[]).every((s:any)=>s.content_level==='metadata_only')
  return <Card title='Извлечённые знания (AI)'>{!knowledge?<p className='sub'>AI пока не извлёк знания. Нажмите «Обновить контекст».</p>:<>{metadataOnly&&emptyMajor&&<div className='hint-card'><b>Знания почти не извлечены.</b><p>Документы/ссылки доступны только как метаданные. Для полного анализа нужен извлечённый текст или ручное описание.</p></div>}{groups.map(([label,keys])=>{const items=keys.flatMap(k=>Array.isArray(knowledge?.[k])?knowledge[k]:[]);return <div key={label} className='knowledge-group'><div className='knowledge-group__title'>{label} ({items.length})</div><div className='knowledge-pills'>{items.slice(0,8).map((x:any,i:number)=><span className='knowledge-pill' key={i}>{String(x)}</span>)}</div></div>})}{missing.length>0&&<div className='hint-card'><b>Чего не хватает</b><ul>{missing.map((m:string,i:number)=><li key={i}>{m}</li>)}</ul></div>}</>}</Card>
}
