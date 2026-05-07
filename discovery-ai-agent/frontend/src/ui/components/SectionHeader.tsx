export default function SectionHeader({ title, subtitle }: { title: string; subtitle?: string }) {
  return <div><h3>{title}</h3>{subtitle ? <p className='sub'>{subtitle}</p> : null}</div>
}
