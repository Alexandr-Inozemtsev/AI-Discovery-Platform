import { ButtonHTMLAttributes, ReactNode } from 'react'
export default function Button({children,className='',variant='secondary',...props}:{children:ReactNode,variant?:'primary'|'secondary'|'ghost'|'soft'|'danger'|'icon',className?:string}&ButtonHTMLAttributes<HTMLButtonElement>){
  return <button {...props} className={`ui-btn ${variant} ${className}`}>{children}</button>
}
