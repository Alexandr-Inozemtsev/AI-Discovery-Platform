import { ReactNode } from 'react'
export default function Card({children,className=''}:{children:ReactNode,className?:string}){return <div className={`ui-card ${className}`}>{children}</div>}
