# Операционная модель глобальных Codex-агентов

## Назначение

Модель описывает, как глобальные Codex delivery agents помогают разрабатывать AI Discovery Platform. Они работают как роли в Codex и не являются runtime-агентами продукта.

## Базовый процесс

1. Пользователь формулирует бизнес/техническую задачу.
2. `ai-orchestrator` анализирует задачу и определяет тип: discovery, delivery, bugfix, review, release, documentation, devops, security, performance, data, LLM/RAG.
3. `ai-orchestrator` выбирает нужных агентов.
4. `ai-orchestrator` формирует набор Codex-задач для агентов.
5. Каждый агент работает только в своей зоне ответственности.
6. Результат передается следующему агенту через handoff.
7. `ai-code-reviewer` проверяет изменения, риски, тесты и границы scope.
8. `ai-qa-engineer` и/или `ai-test-automation-engineer` проверяют тесты, регрессии и acceptance criteria.
9. `ai-delivery-project-manager` обновляет delivery plan и Gantt, если меняются сроки, этапы или зависимости.
10. `ai-trello-analyst` готовит или обновляет Trello-карточки/manual import package.
11. `ai-release-manager` готовит release notes, readiness checklist и rollback plan.
12. `ai-orchestrator` формирует итоговый отчет на русском языке.

## Последовательное подключение

- Discovery-задачи идут через `ai-product-orchestrator`, `ai-business-analyst`, `ai-system-analyst`, затем `ai-solution-architect`.
- Реализация после анализа идет к профильным агентам: backend, frontend, database, LLM/RAG, devops.
- Проверки идут после изменений: `ai-code-reviewer`, затем QA/test automation.
- Release readiness выполняется после успешных проверок.

## Параллельная работа

Параллельно можно выполнять независимые задачи, если они не меняют одни и те же файлы и имеют общий architecture/context handoff:

- backend endpoint и frontend экран после утвержденного API contract;
- документация и QA checklist после стабилизации требований;
- Trello package и Gantt после фиксации scope.

## Запрет конфликтующих изменений

- Два агента не должны одновременно менять один файл без явного владельца изменения.
- Один агент не должен переписывать работу другого без review и причины в отчете.
- Изменение scope требует обновления backlog/Trello/Gantt документов.
- Runtime-код продуктовых агентов нельзя менять в рамках delivery-agent документации.

## Обязательное подключение архитектора

Если задача затрагивает backend + frontend + DB, обязательно подключается `ai-solution-architect`. Он фиксирует API/data contract, migration impact, rollout и rollback.

## LLM/security правило

Если задача затрагивает LLM, prompts, external provider, secrets, privacy или передачу данных наружу, обязательно подключаются `ai-llm-rag-engineer` и `ai-security-reviewer`.

## Итоговый отчет

Любой результат должен описывать: что сделано, какие файлы изменены, какие агенты участвовали, какие gates пройдены, какие риски остались и что делать дальше.

