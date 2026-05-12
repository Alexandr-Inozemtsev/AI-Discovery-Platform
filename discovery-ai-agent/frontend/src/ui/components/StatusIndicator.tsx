export default function StatusIndicator({ status }: { status: 'connected' | 'error' | 'mock' | 'not_configured' }) {
  const map = {
    connected: { label: 'Подключено', cls: 'ready' },
    error: { label: 'Ошибка подключения', cls: 'error' },
    mock: { label: 'Режим mock', cls: 'warning' },
    not_configured: { label: 'Не настроено', cls: 'progress' }
  } as const
  const item = map[status]
  return <span className={`ui-badge ${item.cls}`}>{item.label}</span>
}
