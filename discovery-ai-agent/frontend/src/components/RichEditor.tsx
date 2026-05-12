import Placeholder from '@tiptap/extension-placeholder'
import Link from '@tiptap/extension-link'
import TaskItem from '@tiptap/extension-task-item'
import TaskList from '@tiptap/extension-task-list'
import Underline from '@tiptap/extension-underline'
import { EditorContent, useEditor } from '@tiptap/react'
import StarterKit from '@tiptap/starter-kit'
import Button from '../ui/components/Button'

export default function RichEditor({value,onChange}:{value:string,onChange:(html:string,json:any)=>void}){
  const editor = useEditor({
    extensions:[StarterKit,Underline,Link,TaskList,TaskItem,Placeholder.configure({placeholder:'Начните заполнять раздел...'})],
    content:value,
    onUpdate:({editor})=>onChange(editor.getHTML(), editor.getJSON())
  })
  if(!editor) return null
  return <div className='ui-card'>
    <div className='toolbar'>
      <Button variant='secondary' size='sm' onClick={()=>editor.chain().focus().toggleBold().run()}>B</Button>
      <Button variant='secondary' size='sm' onClick={()=>editor.chain().focus().toggleItalic().run()}>I</Button>
      <Button variant='secondary' size='sm' onClick={()=>editor.chain().focus().toggleUnderline().run()}>U</Button>
      <Button variant='secondary' size='sm' onClick={()=>editor.chain().focus().toggleHeading({level:1}).run()}>H1</Button>
      <Button variant='secondary' size='sm' onClick={()=>editor.chain().focus().toggleBulletList().run()}>• List</Button>
      <Button variant='secondary' size='sm' onClick={()=>editor.chain().focus().toggleOrderedList().run()}>1. List</Button>
      <Button variant='secondary' size='sm' onClick={()=>editor.chain().focus().toggleBlockquote().run()}>Quote</Button>
      <Button variant='secondary' size='sm' onClick={()=>editor.chain().focus().toggleCodeBlock().run()}>Code</Button>
      <Button variant='secondary' size='sm' onClick={()=>editor.chain().focus().undo().run()}>↶</Button>
      <Button variant='secondary' size='sm' onClick={()=>editor.chain().focus().redo().run()}>↷</Button>
    </div>
    <EditorContent editor={editor} className='editor-content'/>
  </div>
}
