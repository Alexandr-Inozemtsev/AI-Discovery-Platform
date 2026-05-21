# Prompt pack: backend

## Назначение
Задачи FastAPI/backend: API, services, validation, errors, tests.

## Каких агентов подключать
`ai-solution-architect`, `ai-backend-developer`, `ai-code-reviewer`, `ai-qa-engineer`; при DB impact - `ai-database-engineer`; при LLM/security impact - `ai-llm-rag-engineer`, `ai-security-reviewer`.

## Последовательность работы
Architecture/API contract -> backend implementation -> tests -> review -> QA -> docs.

## Шаблон Codex-запроса
```text
Ты ai-backend-developer. Реализуй backend-задачу по контракту, не меняй runtime-агентов продукта вне scope, добавь проверки и подготовь handoff для review/QA.
```

## Expected output
Backend diff, тесты/команды, риски, rollback impact.

## Quality gate
Backend gate, Architecture gate при cross-layer изменении, QA gate.

