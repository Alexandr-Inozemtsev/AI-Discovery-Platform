import { ReactNode } from 'react'

export default function AppShell({ sidebar, header, children }: { sidebar: ReactNode; header: ReactNode; children: ReactNode }) {
  return (
    <div className='ui-shell'>
      <aside className='ui-sidebar'>{sidebar}</aside>
      <main className='ui-main'>
        <header className='ui-top-header'>{header}</header>
        <div className='ui-content'>{children}</div>
      </main>
    </div>
  )
}
