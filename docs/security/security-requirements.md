# Требования безопасности AI Discovery Platform

Дата: 2026-05-17

## Цель

Зафиксировать требования к безопасной работе AI Discovery Platform в корпоративном контуре: локальный запуск, контролируемые LLM providers, приватность данных, защита от prompt injection, аудит и управляемые интеграции.

## Риски LLM

- Передача конфиденциальных данных во внешний LLM provider.
- Prompt injection через загруженные документы или ссылки.
- Hallucination без опоры на источники.
- Необъяснимые результаты без traceability.
- Раскрытие system prompt, API key или внутренних endpoint-ов.
- Неконтролируемое использование внешних connectors.

## Секреты и API keys

Требования:
- API keys не хранятся в документации, логах и Trello.
- В UI показывается только masked key.
- `.env` не должен попадать в git.
- Ошибки provider не должны содержать полный ключ.
- Для production нужен secret storage, а не открытый SQLite/plain env.

## Data privacy

- До отправки в LLM данные проходят policy check.
- В LLM передаются только необходимые chunks, а не весь корпус документов.
- Для sensitive data нужна redaction policy.
- External providers должны быть явно разрешены администратором.
- Corporate OpenAI-compatible endpoint является предпочтительным для закрытого контура.

## Prompt injection controls

- Загруженные документы считаются недоверенным input.
- Инструкции из документов не должны переопределять system/developer prompt.
- Retriever возвращает chunks как evidence, а не как команды.
- Agent prompt должен явно отделять контекст от инструкций.
- Результат агента проверяется Critic/validation step на признаки противоречий и неподтверждённых утверждений.

## External connectors

- Trello, GitHub, LLM и будущие RAG adapters подключаются только через allowlist.
- Любой connector должен иметь описание scope, credentials, data flow и audit events.
- Новые dependencies требуют ADR и license/dependency gate.

## Access control backlog

- Ввести роли: владелец проекта, аналитик, разработчик, QA, администратор, аудитор.
- Ограничить изменение LLM settings ролью администратора.
- Ограничить export DOCX для закрытых проектов.
- Добавить workspace/project-level permissions.
- Добавить audit view для security reviewer.

## Audit requirements

Логировать:
- кто загрузил источник;
- какие chunks были отправлены в LLM;
- какой provider/model использовался;
- какой prompt version применялся;
- какие warnings/errors возникли;
- кто экспортировал DOCX;
- кто изменил LLM settings.

## Security backlog

| ID | Задача | Приоритет | Этап |
|---|---|---|---|
| SEC-01 | Описать data policy для LLM payload | P0 | MVP |
| SEC-02 | Добавить audit event model | P0 | MVP |
| SEC-03 | Добавить prompt injection checklist | P0 | MVP |
| SEC-04 | Ввести роли и права проекта | P1 | MMP |
| SEC-05 | Добавить secret storage для production | P1 | MMP |
| SEC-06 | Ввести SBOM/license gate | P1 | MMP |
