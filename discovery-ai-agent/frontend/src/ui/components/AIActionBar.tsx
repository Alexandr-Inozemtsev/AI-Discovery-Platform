import Button from './Button'

type Action = { key:string; label:string; onClick?:()=>void; enabled:boolean }
export default function AIActionBar({actions,loading}:{actions:Action[];loading:string|null}){
  return <div className='ai-action-bar'>{actions.map(a=><Button key={a.key} variant='soft' disabled={!a.enabled || !!loading} onClick={a.onClick} title={a.enabled?'': 'Будет доступно после реализации backend'}>{loading===a.key?'Выполняется…':a.label}</Button>)}</div>
}
