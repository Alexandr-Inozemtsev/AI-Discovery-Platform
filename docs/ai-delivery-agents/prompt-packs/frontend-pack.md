# Prompt pack: frontend

## Назначение
Задачи React/frontend: screens, forms, state, API integration, visual fixes.

## Каких агентов подключать
`ai-ui-ux-designer`, `ai-frontend-developer`, `ai-code-reviewer`, `ai-qa-engineer`; при API change - `ai-system-analyst` и `ai-backend-developer`.

## Последовательность работы
UX/screen spec -> frontend implementation -> browser/build smoke -> review -> QA.

## Шаблон Codex-запроса
```text
Ты ai-frontend-developer. Реализуй frontend-задачу по UX/API contract, проверь build/browser smoke и зафиксируй результат на русском.
```

## Expected output
Frontend diff, screenshots при UI изменениях, test output, risks.

## Quality gate
Frontend gate, QA gate, Documentation gate.

