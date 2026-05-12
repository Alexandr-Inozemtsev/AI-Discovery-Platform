import { ReactNode } from 'react'
import { Link } from 'react-router-dom'

type Variant = 'primary' | 'secondary' | 'soft' | 'ghost' | 'danger' | 'icon'
type Size = 'sm' | 'md' | 'lg'

export default function ButtonLink({ children, to, href, variant='secondary', size='md', fullWidth=false, className='' }: {children:ReactNode;to?:string;href?:string;variant?:Variant;size?:Size;fullWidth?:boolean;className?:string}) {
  const cls = `ui-btn ui-btn--${variant} ui-btn--${size} ${fullWidth?'ui-btn--full':''} ${className}`.trim()
  if (to) return <Link to={to} className={cls}>{children}</Link>
  return <a href={href} className={cls}>{children}</a>
}
