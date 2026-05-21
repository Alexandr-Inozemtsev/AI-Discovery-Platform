# Design documentation AI Discovery Platform

AI Discovery Platform использует глобального `ai-designer` как alias для `ai-ui-ux-designer`. Глобального агента не копировать в проект.

## Workflow
- Соблюдать существующий UI Kit и текущую структуру frontend.
- Любые новые экраны сначала делать как prototype/mockup route в существующем frontend stack.
- Не ломать текущий frontend и не смешивать design prototype с production implementation.
- Сохранять markdown screen spec в `docs/design/screens/`.
- Сохранять PNG screenshots в `docs/design/screenshots/`.
- Если screenshots невозможны, фиксировать `FAILED`, reason, error details и next action.

## Source of truth
Основной source of truth: `docs/design/**`, coded prototype и PNG screenshots. Figma optional.
