import Button from './Button'
export default function StageTabs({tabs,active,onChange}:{tabs:{key:string,label:string}[],active:string,onChange:(k:string)=>void}){return <div className='ui-stage-tabs'>{tabs.map(t=><Button key={t.key} size='sm' variant='ghost' onClick={()=>onChange(t.key)} className={`ui-stage-tab ${active===t.key?'active':''}`}>{t.label}</Button>)}</div>}
