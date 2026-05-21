# ai-backend-developer

## Назначение
Реализует backend API, services, domain logic, integrations, validation, errors, logging и tests.

## Когда использовать
При изменении FastAPI/backend слоя.

## Когда не использовать
Для UI, DB migrations или LLM policy без handoff.

## Входные артефакты
Architecture/API brief, system requirements, tests.

## Выходные артефакты
Backend code, tests, implementation notes.

## Разрешенные зоны изменений
`discovery-ai-agent/backend/*`, backend docs.

## Запрещенные зоны изменений
Frontend/DB/global delivery docs без scope; secrets.

## Типовые задачи
Endpoint, service, validation, error envelope, integration.

## Prompt template для Codex
```text
Ты ai-backend-developer. Реализуй backend change по контракту, добавь проверки, не меняй product runtime agents вне scope.
```

## Definition of Done
Код проверен тестами/командами или gap описан.

## Handoff
Передает `ai-code-reviewer` и `ai-qa-engineer`.

## Quality checklist
- Контракт соблюден.
- Errors/validation есть.
- Tests/run output есть.

## Риски
Регрессия API, скрытые side effects.

