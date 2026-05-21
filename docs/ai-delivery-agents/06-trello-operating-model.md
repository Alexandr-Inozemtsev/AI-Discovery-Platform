# Trello operating model

## Назначение

Документ описывает, как глобальные Codex delivery agents ведут Trello/backlog для разработки AI Discovery Platform. Это не runtime-функция продукта.

## Важное ограничение

Если Trello API не подключен и нет фактического подтверждения через API/UI, агент НЕ должен утверждать, что доска создана или карточки синхронизированы. В этом случае `ai-trello-analyst` готовит manual import package в Markdown.

## Целевая структура доски

1. `01 Product Backlog`
2. `02 Discovery / Analysis`
3. `03 Architecture / ADR`
4. `04 Ready for Development`
5. `05 In Progress`
6. `06 Code Review`
7. `07 QA / Testing`
8. `08 Ready for Release`
9. `09 Done`
10. `10 Blocked`

## Labels

- `Product`
- `Architecture`
- `Backend`
- `Frontend`
- `Database`
- `LLM/RAG`
- `Security`
- `QA`
- `DevOps`
- `Docs`
- `Release`
- `Risk`
- `MVP`

## Структура карточки

- Title.
- Description на русском языке.
- Responsible agent.
- Priority: `P0`, `P1`, `P2`, `P3`.
- Labels.
- Checklist.
- Dependencies.
- Acceptance criteria.
- Definition of Done.
- Sync status: `manual-draft`, `ready-for-import`, `synced-confirmed`, `blocked`.

## Checklist

Минимальный checklist карточки:

- Scope подтвержден.
- Входные документы указаны.
- Acceptance criteria указаны.
- Responsible agent указан.
- Dependencies указаны.
- Quality gate указан.
- Test/documentation expectations указаны.
- DoD указан.

## Responsible agent

Ответственный агент - глобальный Codex delivery agent, например `ai-backend-developer` или `ai-trello-analyst`. Он не является runtime-агентом продукта.

## Правило изменения scope

Любая задача Codex, которая меняет scope проекта, должна обновлять backlog/Trello-cards document. Если API Trello недоступен, обновляется Markdown manual import package.

