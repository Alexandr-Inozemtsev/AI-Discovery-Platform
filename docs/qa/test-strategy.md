# Стратегия тестирования AI Discovery Platform

Дата: 2026-05-17

## Цель

Обеспечить проверяемость платформы от загрузки контекста до финального БТ и DOCX export, включая AI runtime, retrieval, UI flows и корпоративные ограничения.

## Test pyramid

- Unit tests: функции extraction, split chunks, runtime DTO, scoring SimpleRetriever, formatters.
- Integration tests: FastAPI endpoints, repositories, LLM settings, DOCX export.
- Contract tests: API schemas, `AgentResult`, `RetrievalHit`, artifact structures.
- E2E tests: frontend flows create project -> context -> problem -> final BT -> export.
- Exploratory tests: quality of AI output, source trace, readiness, prompt injection samples.

## Обязательные области тестирования

### Content extraction

- TXT UTF-8 и cp1251.
- MD с заголовками.
- CSV с разделителями comma/semicolon/tab.
- DOCX с paragraphs и tables.
- PDF с несколькими страницами.
- XLSX с несколькими листами.
- Неподдерживаемый XLS.
- Файл больше лимита.
- Пустой файл.

### ContextIngestionAgent

- Извлекает knowledge из ручного контекста и chunks.
- Возвращает coverage/readiness/source_trace.
- Отмечает missing information.
- Не падает при частично ошибочных источниках.

### SimpleRetriever

- Возвращает top-k chunks.
- Учитывает фильтры по source type/stage.
- Возвращает score и metadata.
- Не возвращает пустые или неподтверждённые chunks.

### Problem generation

- Использует context readiness.
- Возвращает проблему, боли, root causes, assumptions.
- Сохраняет source trace.
- Работает с AI questions и ответами пользователя.

### LLM settings

- Mock provider готов без ключа.
- OpenRouter/corporate provider требует base URL, model и key.
- Key маскируется.
- Ошибки 401, timeout, model_not_found показываются понятно.

### DOCX export

- Экспорт содержит все обязательные разделы.
- Пустые разделы отмечены.
- Source trace включён в приложение.
- Русские символы отображаются корректно.

### Frontend flows

- Создание проекта.
- Открытие проекта.
- Загрузка файлов.
- Обновление контекста.
- Генерация проблемы.
- Сохранение артефакта.
- Экспорт DOCX.
- Ошибки backend/LLM отображаются пользователю.

## Acceptance criteria для эпиков

- Каждый эпик имеет минимум smoke scenario.
- P0 эпики имеют unit/integration coverage.
- LLM/RAG эпики имеют тесты fallback и invalid JSON.
- Security эпики имеют checklist тестов на prompt injection и secrets.
- UI эпики имеют проверки loading/error/empty/blocked/warning/ready states.

## Test data

- Малый DOCX с таблицей.
- PDF с русским текстом.
- CSV с KPI.
- XLSX с несколькими листами.
- Документ с prompt injection фразами.
- Набор контекста с недостаточной готовностью.

## Quality gate перед release

- Все обязательные tests проходят.
- Нет failing smoke.
- Нет незакрытых P0/P1 defects.
- Validation report не содержит критичных пропусков.
- Security reviewer подтвердил отсутствие секретов в repo и logs.
