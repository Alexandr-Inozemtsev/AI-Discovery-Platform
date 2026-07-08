import { Bot, CheckCircle2, ClipboardCheck, FileText, HelpCircle, ListChecks, MessageSquareText, Send, Sparkles } from 'lucide-react'
import type { ArtifactType, AssistantAction, AssistantMessage } from '../../types/discovery'
import Button from './Button'

type SuggestedActionKey = 'apply' | 'open_stage' | 'show_sources' | 'ask_questions' | 'quality_check' | 'export_docx'

type Props = {
  activeStage: ArtifactType
  stageLabel: string
  messages: AssistantMessage[]
  input: string
  loading?: boolean
  applying?: boolean
  error?: string
  pendingAction?: AssistantAction | null
  onInputChange: (value: string) => void
  onSend: (message?: string) => void
  onSuggestedAction: (action: SuggestedActionKey) => void
}

const actionLabels: Record<SuggestedActionKey, string> = {
  apply: 'Применить в артефакт',
  open_stage: 'Открыть этап',
  show_sources: 'Показать источники',
  ask_questions: 'Задать уточняющие вопросы',
  quality_check: 'Проверить качество',
  export_docx: 'Экспортировать DOCX',
}

const actionIcons: Record<SuggestedActionKey, JSX.Element> = {
  apply: <CheckCircle2 size={15} />,
  open_stage: <ListChecks size={15} />,
  show_sources: <FileText size={15} />,
  ask_questions: <HelpCircle size={15} />,
  quality_check: <ClipboardCheck size={15} />,
  export_docx: <FileText size={15} />,
}

const formatValue = (value: unknown): string => {
  if (value == null) return '—'
  if (typeof value === 'string') return value
  if (typeof value === 'number' || typeof value === 'boolean') return String(value)
  return JSON.stringify(value, null, 2)
}

const changedFields = (action?: AssistantAction | null) => {
  const fromPreview = action?.preview?.changed_fields
  if (Array.isArray(fromPreview)) return fromPreview.map(String)
  return Object.keys(action?.proposed_patch || {})
}

const artifactLabels: Record<ArtifactType, string> = {
  CONTEXT: 'Контекст',
  PROBLEM: 'Проблема',
  GOAL: 'Цель',
  BUSINESS_EFFECT: 'Бизнес-эффект',
  AS_IS: 'AS IS',
  TO_BE: 'TO BE',
  USE_CASES: 'Use Cases',
  FUNCTIONAL_REQUIREMENTS: 'Требования',
  NON_FUNCTIONAL_REQUIREMENTS: 'Нефункциональные требования',
  RISKS: 'Риски',
  GLOSSARY: 'Глоссарий',
  FINAL_BT: 'Финальный БТ',
  VALIDATION_REPORT: 'Отчёт проверки',
}

export type { SuggestedActionKey }

export default function AIAssistantPanel({
  activeStage,
  stageLabel,
  messages,
  input,
  loading = false,
  applying = false,
  error,
  pendingAction,
  onInputChange,
  onSend,
  onSuggestedAction,
}: Props) {
  const canApply = Boolean(pendingAction && pendingAction.status === 'proposed')
  const fields = changedFields(pendingAction)
  const targetStage = pendingAction?.target_artifact_type || activeStage
  const targetStageLabel = targetStage === activeStage ? stageLabel : artifactLabels[targetStage]

  return (
    <aside className='ai-chat-panel' aria-label='AI Discovery Chat'>
      <div className='ai-chat-panel__header'>
        <div>
          <div className='ai-chat-panel__eyebrow'><Sparkles size={14} /> AI Discovery Chat</div>
          <h3>Управление Discovery</h3>
          <p className='sub'>Текущий этап: {stageLabel}</p>
        </div>
        <span className='ui-badge primary'>{artifactLabels[activeStage]}</span>
      </div>

      <div className='ai-chat-actions' aria-label='Быстрые действия AI-чата'>
        {(Object.keys(actionLabels) as SuggestedActionKey[]).map((key) => (
          <Button
            key={key}
            type='button'
            size='sm'
            variant={key === 'apply' ? 'primary' : 'secondary'}
            leftIcon={actionIcons[key]}
            disabled={key === 'apply' && (!canApply || applying)}
            loading={key === 'apply' && applying}
            onClick={() => onSuggestedAction(key)}
          >
            {actionLabels[key]}
          </Button>
        ))}
      </div>

      <div className='ai-chat-history' aria-live='polite'>
        {messages.length === 0 ? (
          <div className='ai-chat-empty'>
            <Bot size={22} />
            <div>
              <b>Начните с задачи для AI</b>
              <p className='sub'>Например: “Сформулируй проблему по текущему контексту” или “Проверь качество требований”.</p>
            </div>
          </div>
        ) : (
          messages.map((message) => (
            <div key={message.id} className={`ai-chat-message ai-chat-message--${message.role}`}>
              <div className='ai-chat-message__role'>{message.role === 'user' ? 'Вы' : 'AI'}</div>
              <div className='ai-chat-message__content'>{message.content}</div>
            </div>
          ))
        )}
      </div>

      {pendingAction ? (
        <div className='ai-chat-preview'>
          <div className='ai-chat-preview__head'>
            <div>
              <b>Предпросмотр изменения</b>
              <p className='sub'>Целевой артефакт: {targetStageLabel}</p>
            </div>
            <span className={`ui-badge ${pendingAction.status === 'applied' ? 'ready' : 'warning'}`}>
              {pendingAction.status === 'applied' ? 'Применён' : 'Ожидает'}
            </span>
          </div>
          {pendingAction.preview?.summary ? <p className='sub'>{String(pendingAction.preview.summary)}</p> : null}
          <div className='ai-chat-diff'>
            {fields.length ? fields.map((field) => (
              <div key={field} className='ai-chat-diff__row'>
                <span className='ai-chat-diff__field'>{field}</span>
                <pre>{formatValue(pendingAction.proposed_patch?.[field])}</pre>
              </div>
            )) : <div className='sub'>Нет изменённых полей для отображения.</div>}
          </div>
        </div>
      ) : null}

      {error ? <div className='ai-chat-error'>{error}</div> : null}

      <form
        className='ai-chat-compose'
        onSubmit={(event) => {
          event.preventDefault()
          onSend()
        }}
      >
        <textarea
          className='ui-textarea'
          value={input}
          onChange={(event) => onInputChange(event.target.value)}
          placeholder='Опишите, что нужно сделать в Discovery-процессе...'
          disabled={loading}
        />
        <Button type='submit' variant='primary' fullWidth disabled={!input.trim() || loading} loading={loading} rightIcon={<Send size={16} />}>
          Отправить
        </Button>
      </form>

      <div className='ai-chat-note'><MessageSquareText size={14} /> Изменение не применяется автоматически. Сначала проверьте предпросмотр.</div>
    </aside>
  )
}
