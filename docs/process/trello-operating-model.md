# Операционная модель Trello для AI Discovery Platform

Дата: 2026-05-17

## Назначение

Trello используется как визуальный delivery-board для развития AI Discovery Platform. Доска не заменяет БТ, ТЗ, ADR и repository documentation, а связывает backlog с рабочим процессом команды.

## Списки

1. `00 Входящие`
2. `01 Продуктовый backlog`
3. `02 Discovery / анализ`
4. `03 Архитектура / ADR`
5. `04 Готово к разработке`
6. `05 В работе`
7. `06 Code Review`
8. `07 QA / проверка`
9. `08 Готово`
10. `09 Заблокировано`

## Роли

- `ai-product-orchestrator`: приоритизация, roadmap, контроль DoR/DoD.
- `ai-business-analyst`: БТ, бизнес-цели, user stories.
- `ai-system-analyst`: ТЗ, API, статусы, ошибки, edge cases.
- `ai-solution-architect`: ADR, архитектурные boundaries, риски.
- `ai-trello-analyst`: структура доски, labels, карточки, checklists.
- Профильные агенты: Backend, Frontend, LLM/RAG, Data, Security, DevOps, QA, Docs.

## Правила карточки

Карточка должна содержать:
- цель;
- описание;
- бизнес-ценность;
- приоритет;
- этап MVP/MMP/Целевой контур;
- ответственный агент;
- dependencies;
- acceptance criteria;
- definition of done;
- labels;
- checklist.

## Workflow

- Новые идеи попадают в `00 Входящие`.
- Orchestrator уточняет формулировку и переносит в `01 Продуктовый backlog`.
- Бизнес- и системные задачи проходят `02 Discovery / анализ`.
- Архитектурные решения проходят `03 Архитектура / ADR`.
- После DoR карточка переносится в `04 Готово к разработке`.
- Реализация идёт через `05 В работе`, `06 Code Review`, `07 QA / проверка`.
- Принятый результат переносится в `08 Готово`.
- Заблокированные карточки переносятся в `09 Заблокировано` с причиной и owner unblock.

## Quality gates

- Нельзя начинать разработку без AC и DoD.
- Нельзя менять API без ADR.
- Нельзя добавлять dependencies без ADR и license gate.
- Нельзя закрывать карточку без обновления документации.
- Нельзя переносить в QA без self-check.

## Связь с документацией

- Product backlog: `docs/backlog/product-backlog.md`.
- Roadmap: `docs/backlog/roadmap.md`.
- Trello import package: `docs/backlog/trello-board-import.md` и `docs/backlog/trello-cards.md`.
- ADR: `docs/architecture/adr-002-target-platform-evolution.md`.
- БТ: `docs/business/bt-ai-discovery-platform-target.md`.
- ТЗ: `docs/system/tz-ai-discovery-platform-target.md`.
