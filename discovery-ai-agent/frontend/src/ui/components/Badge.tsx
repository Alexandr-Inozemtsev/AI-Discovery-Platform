export default function Badge({text,variant='progress'}:{text:string,variant?:'ready'|'progress'|'warning'|'error'}){return <span className={`ui-badge ${variant}`}>{text}</span>}
