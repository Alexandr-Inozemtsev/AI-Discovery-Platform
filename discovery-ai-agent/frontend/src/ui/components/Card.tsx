import { ReactNode } from 'react'

type Props = {
  title?: ReactNode
  subtitle?: ReactNode
  actions?: ReactNode
  footer?: ReactNode
  compact?: boolean
  soft?: boolean
  interactive?: boolean
  className?: string
  children: ReactNode
}

export default function Card({ title, subtitle, actions, footer, compact, soft, interactive, className = '', children }: Props) {
  const cls = ['ui-card', compact ? 'ui-card--compact' : '', soft ? 'ui-card--soft' : '', interactive ? 'ui-card--interactive' : '', className].filter(Boolean).join(' ')
  return (
    <section className={cls}>
      {(title || actions) && (
        <div className='ui-card__head'>
          <div>
            {title ? <h4 className='ui-card__title'>{title}</h4> : null}
            {subtitle ? <div className='ui-card__subtitle'>{subtitle}</div> : null}
          </div>
          {actions ? <div className='ui-actions'>{actions}</div> : null}
        </div>
      )}
      {children}
      {footer ? <div className='ui-card-footer'>{footer}</div> : null}
    </section>
  )
}
