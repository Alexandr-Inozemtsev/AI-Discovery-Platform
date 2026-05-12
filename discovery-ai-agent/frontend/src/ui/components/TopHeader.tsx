import { ReactNode } from 'react'

export default function TopHeader({ left, right }: { left: ReactNode; right: ReactNode }) {
  return <><div>{left}</div><div>{right}</div></>
}
