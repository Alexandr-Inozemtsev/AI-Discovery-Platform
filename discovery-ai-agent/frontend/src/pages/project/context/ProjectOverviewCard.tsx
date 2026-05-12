import Card from '../../../ui/components/Card'

type Props={fields:{label:string;value?:string}[]}
export default function ProjectOverviewCard({fields}:Props){
  return <Card title='Обзор проекта'>{fields.map((f,i)=><div key={i} className='context-field'><div className='context-field__label'>{f.label}</div><div className={`context-field__value ${!f.value?'context-field__placeholder':''}`}>{f.value||'Не заполнено'}</div></div>)}<div className='autosave-row'><span className='status-dot ok'/>Autosave: Сохранено</div></Card>
}
