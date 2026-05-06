import React from 'react'

type Props = { children: React.ReactNode; fallbackTitle?: string }
type State = { hasError: boolean }

export default class ErrorBoundary extends React.Component<Props, State> {
  state: State = { hasError: false }

  static getDerivedStateFromError(): State {
    return { hasError: true }
  }

  componentDidCatch(error: Error) {
    console.error('UI ErrorBoundary:', error)
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className='card'>
          <h3 style={{ marginTop: 0 }}>{this.props.fallbackTitle || 'Ошибка интерфейса'}</h3>
          <p className='sub'>Произошла ошибка рендеринга. Обновите страницу или откройте другой этап.</p>
        </div>
      )
    }
    return this.props.children
  }
}
