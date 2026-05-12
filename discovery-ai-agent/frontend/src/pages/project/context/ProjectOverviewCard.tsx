import Card from '../../../ui/components/Card'

type OverviewField = { key: string; label: string; value?: string; placeholder: string; helper: string }
type Props={fields:OverviewField[];onChange:(key:string,value:string)=>void}
export default function ProjectOverviewCard({fields,onChange}:Props){
  return <Card title='Обзор проекта'>{fields.map((f)=><div key={f.key} className='context-field'><div className='context-field__label'>{f.label}</div><input className='ui-input' value={f.value||''} placeholder={f.placeholder} onChange={e=>onChange(f.key,e.target.value)}/><div className='context-field__helper'>{f.helper}</div></div>)}<div className='autosave-row'><span className='status-dot ok'/>Autosave: Сохранено</div></Card>
}
