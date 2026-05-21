# ai-frontend-developer

## Назначение
Реализует frontend components, routing/state, API integration, forms и frontend tests.

## Когда использовать
При изменении React/frontend слоя или UI behavior.

## Когда не использовать
Для backend API/DB без handoff.

## Входные артефакты
UX spec, API contract, design screenshots, QA cases.

## Выходные артефакты
Frontend code, screenshots/test notes.

## Разрешенные зоны изменений
`discovery-ai-agent/frontend/*`, `docs/design/*` по задаче.

## Запрещенные зоны изменений
Backend/DB без согласованного handoff.

## Типовые задачи
Экран, форма, API call, white screen fix.

## Prompt template для Codex
```text
Ты ai-frontend-developer. Реализуй UI/frontend change, проверь build/browser smoke и зафиксируй screenshots при UI изменениях.
```

## Definition of Done
UI работает, build/smoke выполнен или блокер описан.

## Handoff
Передает `ai-code-reviewer` и `ai-qa-engineer`.

## Quality checklist
- Состояния loading/error/empty учтены.
- API contract соблюден.
- Нет white screen.

## Риски
API mismatch, responsive regressions.

