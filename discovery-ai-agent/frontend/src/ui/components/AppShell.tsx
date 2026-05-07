import { ReactNode } from 'react'
export default function AppShell({sidebar,header,children}:{sidebar:ReactNode,header:ReactNode,children:ReactNode}){return <div className='ui-shell'><aside>{sidebar}</aside><main><div>{header}</div><div className='ui-content'>{children}</div></main></div>}
