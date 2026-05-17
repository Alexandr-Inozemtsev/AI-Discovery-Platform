# Окружения, запуск и CI/CD AI Discovery Platform

Дата: 2026-05-17

## Целевые окружения

| Окружение | Назначение | Особенности |
|---|---|---|
| local | Работа аналитика или разработчика на одной машине | Windows без Docker, SQLite, mock или корпоративный LLM |
| dev | Интеграционная разработка | Docker Compose, тестовые ключи, dev database |
| test | Автотесты и QA | фиксированные test fixtures, mocked LLM |
| stage | Предрелизная проверка | production-like config, restricted data |
| prod | промышленный контур | secret storage, audit, backups, monitoring |

## Локальный запуск без Docker для Windows

Текущий сценарий:
- открыть `discovery-ai-agent`;
- запустить `start.bat`;
- backend работает на `http://localhost:8000`;
- frontend работает на `http://localhost:5173`;
- SQLite хранится в `backend/data/discovery_agent.db`.

Требования:
- понятные ошибки при занятых портах;
- проверка Python/Node versions;
- инструкция очистки локальных данных;
- запрет записи секретов в git;
- mock LLM как безопасный режим по умолчанию.

## Docker запуск

Назначение:
- повторяемый dev/prod запуск;
- изоляция backend/frontend;
- упрощение CI и stage deployments.

Требования:
- отдельные env files для dev/test/stage/prod;
- health checks backend/frontend;
- volume для SQLite или переход на управляемую БД в production;
- явные limits для file upload и worker timeouts.

## CI/CD backlog

1. Backend unit tests.
2. Backend integration tests для API.
3. Content extraction tests.
4. Agent runtime tests.
5. Frontend build.
6. Frontend lint/typecheck.
7. E2E smoke для create project -> context -> problem -> export.
8. Dependency license check.
9. Secret scan.
10. Docker image build.
11. Release notes generation.

## Quality gates

- Нет изменения API-контрактов без ADR.
- Нет новых dependencies без ADR и license gate.
- Все tests/lint/build проходят.
- Security requirements проверены.
- Документация обновлена.
- Trello-карточка имеет AC/DoD и переведена в QA только после self-check.

## Rollback

- Для документации: откат конкретных Markdown-файлов.
- Для backend migrations: отдельный downgrade plan.
- Для LLM/RAG adapters: feature flag и отключение adapter.
- Для frontend: rollback release artifact.

## Monitoring backlog

- Backend health.
- LLM provider status.
- Agent run errors.
- Extraction failures.
- DOCX export failures.
- Latency по этапам.
- Invalid JSON rate.
