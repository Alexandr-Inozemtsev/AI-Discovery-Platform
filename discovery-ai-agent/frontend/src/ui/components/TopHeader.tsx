import { ReactNode } from 'react'

export default function TopHeader({ left, right }: { left: ReactNode; right: ReactNode }) {
  return (
    <>
      <div className='ui-top-header__left'>{left}</div>
      <div className='ui-top-header__right'>{right}</div>
    </>
  )
}
