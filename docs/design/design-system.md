# Design system AI Discovery Platform

## Назначение

Документ фиксирует целевой визуальный язык MVP и corporate-ready версии AI Discovery Platform. Это дизайн-документация, а не изменение frontend implementation.

## Визуальный стиль

- Enterprise SaaS: спокойный, плотный, рабочий интерфейс.
- Основной акцент: управляемость Discovery, traceability, readiness, AI-assist.
- Без маркетинговых hero-блоков внутри workspace.
- Приоритет: сканируемость, предсказуемая навигация, ясные статусы.

## Tokens

| Token | Значение | Назначение |
|---|---|---|
| `color.bg` | `#F6F8FB` | Фон приложения |
| `color.surface` | `#FFFFFF` | Основные панели и карточки |
| `color.text` | `#172033` | Основной текст |
| `color.muted` | `#667085` | Вторичный текст |
| `color.primary` | `#2457D6` | Основные действия |
| `color.success` | `#138A4B` | Ready/completed |
| `color.warning` | `#B7791F` | Warning/stale |
| `color.error` | `#C0362C` | Error/blocked |
| `color.ai` | `#6B4EFF` | AI-сценарии |
| `font.family` | Inter/system sans | UI и презентационные подписи |
| `font.size.body` | 14-16 px | Основной текст |
| `font.size.caption` | 12-13 px | Метаданные |
| `spacing.unit` | 8 px | Базовый шаг |
| `radius.card` | 8 px | Карточки и панели |
| `shadow.panel` | low elevation | Только для модальных/верхних панелей |

## UI components

### Button

Варианты: primary, secondary, ghost, icon. Primary используется только для ключевого действия экрана. Icon buttons должны иметь tooltip/aria-label.

### Card

Используется для повторяемых сущностей: проекты, sources, knowledge cards, risk items. Не вкладывать карточки в карточки.

### StageTabs

Навигация Discovery stages: Context, Problem, Goal, Business Effect, AS IS, TO BE, Use Cases, Requirements, Risks, Final BT.

### StatusIndicator

Показывает `ready`, `warning`, `error`, `stale`, `metadata-only`, `empty`. Должен иметь текстовое пояснение на русском.

### AIActionBar

Компактная панель AI-действий: generate, ask, apply patch, validate. Все AI-действия должны явно показывать состояние выполнения и ошибку.

### Source list

Список источников контекста: файлы, ссылки, Confluence/RAG results. Обязательные поля: title, type, status, chunks count, updatedAt, errorMessage.

### Knowledge cards

Карточки extracted knowledge: facts, assumptions, missing information, source references.

### Readiness badges

Badges readiness: ready, warning, blocked. Должны связываться с missing information и next actions.

## States

| State | Значение | UI-поведение |
|---|---|---|
| `loading` | Запрос выполняется | Skeleton или spinner с русским текстом. |
| `empty` | Нет данных | Пустое состояние с основным действием. |
| `error` | Ошибка запроса или обработки | Красный статус, human message, next action. |
| `warning` | Есть риск или неполнота | Желтый статус, что исправить. |
| `ready` | Данные готовы | Зеленый статус, переход к следующему шагу. |
| `stale` | Downstream устарел после upstream change | Желтый статус, предложить regeneration/validation. |
| `metadata-only` | Есть metadata, но нет извлеченного текста | Серый/желтый статус, объяснить ограничение. |

## Связанные документы

- [Context screen spec](context-screen-spec.md)
- [Screen inventory](screen-inventory.md)
- [ТЗ](../system/tz-ai-discovery-platform-target.md)
- [RAG target design](../llm-rag/rag-and-retrieval-target-design.md)

