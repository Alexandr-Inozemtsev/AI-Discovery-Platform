import { ReactNode } from 'react'
export default function TopHeader({left,right}:{left:ReactNode,right:ReactNode}){return <div className='ui-top-header'><div>{left}</div><div>{right}</div></div>}
