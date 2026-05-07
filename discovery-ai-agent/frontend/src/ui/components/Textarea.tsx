import { TextareaHTMLAttributes } from 'react'
export default function Textarea(props:TextareaHTMLAttributes<HTMLTextAreaElement>){return <textarea {...props} className={`ui-textarea ${props.className||''}`}/>} 
