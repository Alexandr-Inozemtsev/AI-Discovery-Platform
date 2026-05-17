# Структура Trello-доски AI Discovery Platform

Дата: 2026-05-17

## Назначение

Документ описывает структуру Trello-доски для delivery-процесса AI Discovery Platform. Он пригоден для ручного переноса, если автоматическая Trello-интеграция недоступна, и является контрольным списком для проверки автоматического оформления доски.

## Целевая доска

- URL: https://trello.com/b/AKdFcJsw/aidiscoveryplatform
- Название: AI_Discovery_platform
- Язык всех списков, labels, карточек и checklists: русский.

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

## Labels

| Label | Назначение |
|---|---|
| Продукт | Продуктовые решения и roadmap |
| Бизнес-анализ | БТ, бизнес-цели, user stories |
| Системный анализ | ТЗ, API, модели, статусы |
| Архитектура | ADR, runtime, boundaries |
| Backend | FastAPI, services, agents |
| Frontend | React UI, UX states |
| LLM/RAG | LLM providers, retrieval, prompts |
| Данные | Data model, migrations, storage |
| Безопасность | Secrets, privacy, prompt injection |
| DevOps | Environments, CI/CD, Docker |
| QA | Test strategy, acceptance checks |
| Документация | Docs, user guide, runbook |
| Trello | Board operations and workflow |
| ADR | Architecture decision records |
| БТ | Бизнес-требования |
| ТЗ | Техническое задание |
| MVP | MVP scope |
| Целевой контур | Future/industrial scope |
| Риск | High-risk item |

## Правила движения карточек

- `00 Входящие`: сырые идеи, замечания, вопросы.
- `01 Продуктовый backlog`: сформулированные эпики и фичи без полной готовности к разработке.
- `02 Discovery / анализ`: задачи уточнения требований, БТ, user stories и acceptance criteria.
- `03 Архитектура / ADR`: архитектурные решения, data model, security, runtime, RAG.
- `04 Готово к разработке`: карточки с DoR, AC, DoD, зависимостями и оценёнными рисками.
- `05 В работе`: активная разработка или подготовка документа.
- `06 Code Review`: проверка изменений production-кода или документации.
- `07 QA / проверка`: тестирование, acceptance checks, smoke/regression.
- `08 Готово`: завершено и принято.
- `09 Заблокировано`: есть внешняя зависимость, риск или открытое решение.

## Definition of Ready для карточки

- Есть цель и бизнес-ценность.
- Указан тип: Эпик, Фича, User Story, Задача или Подзадача.
- Указаны приоритет, этап, ответственный агент и dependencies.
- Есть acceptance criteria и definition of done.
- Проставлены labels.
- Известен целевой список Trello.

## Definition of Done для карточки

- Выполнены checklist items.
- Обновлены связанные документы.
- Проверены ограничения: нет новых dependencies без ADR, нет изменения API без ADR, нет секретов в коде и документах.
- Пройдены назначенные quality gates.
- Результат связан с БТ, ТЗ, ADR или backlog.
