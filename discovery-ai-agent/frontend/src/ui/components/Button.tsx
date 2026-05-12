import { ButtonHTMLAttributes, ReactNode } from 'react'

type ButtonVariant = 'primary' | 'secondary' | 'soft' | 'ghost' | 'danger' | 'icon'
type ButtonSize = 'sm' | 'md' | 'lg'

type Props = {
  children?: ReactNode
  variant?: ButtonVariant
  size?: ButtonSize
  fullWidth?: boolean
  loading?: boolean
  leftIcon?: ReactNode
  rightIcon?: ReactNode
  className?: string
} & ButtonHTMLAttributes<HTMLButtonElement>

export default function Button({
  children,
  variant = 'secondary',
  size = 'md',
  fullWidth = false,
  loading = false,
  leftIcon,
  rightIcon,
  className = '',
  disabled,
  ...props
}: Props) {
  const isDisabled = disabled || loading
  const noVisibleChildren = !children && !loading
  const ariaLabel = props['aria-label'] || (typeof children === 'string' ? children : undefined)

  if (variant === 'icon' && noVisibleChildren && !ariaLabel) {
    console.warn('Button variant="icon" requires aria-label when children are empty.')
  }

  return (
    <button
      {...props}
      aria-label={ariaLabel}
      disabled={isDisabled}
      className={`ui-btn ui-btn--${variant} ui-btn--${size} ${fullWidth ? 'ui-btn--full' : ''} ${loading ? 'ui-btn--loading' : ''} ${className}`.trim()}
    >
      {loading ? <span className='ui-btn__spinner' aria-hidden='true' /> : leftIcon ? <span className='ui-btn__icon'>{leftIcon}</span> : null}
      <span className='ui-btn__label'>{loading ? 'Загрузка...' : children}</span>
      {!loading && rightIcon ? <span className='ui-btn__icon'>{rightIcon}</span> : null}
    </button>
  )
}
