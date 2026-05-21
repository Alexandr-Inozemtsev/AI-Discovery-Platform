# AI Designer Workflow

## Правило проекта
`ai-designer` должен соблюдать существующий UI Kit AI Discovery Platform и не ломать текущий frontend. Новые экраны сначала создаются как prototype/mockup route, затем передаются `ai-frontend-developer`.

## Артефакты
- `docs/design/screens/<screen-name>.md`
- `docs/design/screenshots/<screen-name>-desktop.png`
- `docs/design/screenshots/<screen-name>-tablet.png`, если применимо
- `docs/design/screenshots/<screen-name>-mobile.png`, если применимо
- prototype/mockup route в существующем frontend stack

## Failure handling
Если frontend dev server, Playwright/browser или dependencies недоступны, screen spec должен содержать:

```text
Screenshot generation status: FAILED
Reason:
- ...
Error details:
- ...
Next action:
- ...
```
