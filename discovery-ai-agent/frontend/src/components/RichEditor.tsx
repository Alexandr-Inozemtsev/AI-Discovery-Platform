import Placeholder from '@tiptap/extension-placeholder'
import Link from '@tiptap/extension-link'
import TaskItem from '@tiptap/extension-task-item'
import TaskList from '@tiptap/extension-task-list'
import Underline from '@tiptap/extension-underline'
import { EditorContent, useEditor } from '@tiptap/react'
import StarterKit from '@tiptap/starter-kit'

export default function RichEditor({value,onChange}:{value:string,onChange:(html:string,json:any)=>void}){
  const editor = useEditor({
    extensions:[StarterKit,Underline,Link,TaskList,TaskItem,Placeholder.configure({placeholder:'Начните заполнять раздел...'})],
    content:value,
    onUpdate:({editor})=>onChange(editor.getHTML(), editor.getJSON())
  })
  if(!editor) return null
  return <div className='card'>
    <div className='toolbar'>
      <button className='btn' onClick={()=>editor.chain().focus().toggleBold().run()}>B</button>
      <button className='btn' onClick={()=>editor.chain().focus().toggleItalic().run()}>I</button>
      <button className='btn' onClick={()=>editor.chain().focus().toggleUnderline().run()}>U</button>
      <button className='btn' onClick={()=>editor.chain().focus().toggleHeading({level:1}).run()}>H1</button>
      <button className='btn' onClick={()=>editor.chain().focus().toggleBulletList().run()}>• List</button>
      <button className='btn' onClick={()=>editor.chain().focus().toggleOrderedList().run()}>1. List</button>
      <button className='btn' onClick={()=>editor.chain().focus().toggleBlockquote().run()}>Quote</button>
      <button className='btn' onClick={()=>editor.chain().focus().toggleCodeBlock().run()}>Code</button>
      <button className='btn' onClick={()=>editor.chain().focus().undo().run()}>↶</button>
      <button className='btn' onClick={()=>editor.chain().focus().redo().run()}>↷</button>
    </div>
    <EditorContent editor={editor} className='editor-content'/>
  </div>
}
