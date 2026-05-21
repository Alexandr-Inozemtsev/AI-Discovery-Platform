# Политики взаимодействия агентов

## Ownership policy

Каждый агент владеет только своей зоной ответственности. Backend agent не переписывает UX-решения, frontend agent не меняет миграции без database handoff, Trello agent не меняет production-код.

## Handoff policy

Handoff обязателен, когда результат одного агента становится входом для другого. Формат: контекст, выполненная работа, решения, файлы, риски, pending work, next action.

## Review policy

Изменения кода, архитектуры, безопасности, данных и release-impact проходят review через `ai-code-reviewer` и профильный gate. Review фиксирует blocking и non-blocking issues.

## Conflict resolution policy

При конфликте ownership приоритет такой: требования пользователя, safety boundaries, architecture decision, профильный владелец, review. Конфликт нельзя решать молча.

## Security policy

Нельзя сохранять секреты, API keys, tokens, passwords или private endpoints в репозитории. Изменения LLM provider, auth, внешних интеграций и обработки пользовательских данных требуют `ai-security-reviewer`.

## Prompt quality policy

Prompts должны иметь цель, входные данные, ограничения, expected output, критерии качества и запрет на выдумывание фактов. Для LLM/RAG задач нужен traceability до источников.

## Documentation policy

Все пользовательские документы, backlog, Trello-card descriptions, Gantt comments и отчеты пишутся на русском языке. Иностранные термины переводятся при первом использовании: например, quality gate (контрольная точка качества), handoff (передача результата).

## Trello update policy

Если Trello API не подключен, агент не утверждает, что доска создана. Вместо этого он готовит Markdown manual import package. Любая Codex-задача, меняющая scope проекта, обновляет backlog/Trello-cards document.

## Gantt update policy

Если меняются сроки, этапы, зависимости или release readiness, обновляется `07-gantt-delivery-plan.md`. Mermaid Gantt является draft-планом, а не подключением к внешней системе.

## Backlog update policy

Backlog обновляется при появлении нового scope, изменении приоритета, зависимости, acceptance criteria или Definition of Done.

## No silent change policy

Агент не делает скрытых изменений. Итоговый отчет должен перечислять файлы, причины изменений, gates и остаточные риски.

## Russian language policy

Все delivery-документы, Trello descriptions, Gantt comments, handoff и отчеты ведутся на русском языке. Кодовые идентификаторы, API paths и имена классов можно оставлять на английском.

