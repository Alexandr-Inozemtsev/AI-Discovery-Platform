# Design documentation AI Discovery Platform

AI Discovery Platform использует глобального `ai-designer` как alias для `ai-ui-ux-designer`. Глобального агента не копировать в проект.

## Карта документов

- [UX/UI target spec](ux-ui-target-spec.md) - целевая UX/UI-спецификация.
- [Design system](design-system.md) - tokens, компоненты и состояния.
- [Screen inventory](screen-inventory.md) - список экранов и ожидаемые сценарии.
- [Context screen spec](context-screen-spec.md) - подробная спецификация страницы Контекст.
- [Management presentation visual style](management-presentation-visual-style.md) - визуальный стиль презентации для руководства.
- [ai-designer workflow](ai-designer-workflow.md) - правила работы глобального `ai-ui-ux-designer`.

## Workflow
- Соблюдать существующий UI Kit и текущую структуру frontend.
- Любые новые экраны сначала делать как prototype/mockup route в существующем frontend stack.
- Не ломать текущий frontend и не смешивать design prototype с production implementation.
- Сохранять markdown screen spec в `docs/design/screens/`.
- Сохранять PNG screenshots в `docs/design/screenshots/`.
- Если screenshots невозможны, фиксировать `FAILED`, reason, error details и next action.

## Source of truth
Основной source of truth: `docs/design/**`, coded prototype и PNG screenshots. Figma optional.

## Связанные документы

- [ТЗ целевого состояния](../system/tz-ai-discovery-platform-target.md)
- [Архитектурная документация](../architecture/README.md)
- [Trello backlog](../backlog/trello-cards.md)
- [Gantt delivery plan](../ai-delivery-agents/07-gantt-delivery-plan.md)
