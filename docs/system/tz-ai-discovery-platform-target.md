# Техническое задание: целевое состояние AI Discovery Platform

Дата: 2026-05-17  
Роль подготовки: `ai-system-analyst`  
Статус документа: системное ТЗ для передачи в разработку  
Область документа: целевое состояние на основе фактического React/FastAPI MVP в репозитории

## 1. Назначение системы

AI Discovery Platform предназначена для подготовки, структурирования и проверки материалов Discovery перед передачей инициативы в Delivery. Система помогает пользователю собрать контекст, извлечь знания из источников, сформулировать проблему, цель, бизнес-эффект, use cases, функциональные и нефункциональные требования, риски, финальное БТ и выгрузить результат в DOCX.

Целевое назначение:

- сократить ручную работу бизнес-аналитика и системного аналитика при подготовке Discovery-артефактов;
- обеспечить трассируемость выводов AI до исходных источников через `source_trace`;
- фиксировать готовность контекста через `coverage` и `readiness`;
- поддержать управляемый переход от `CONTEXT` к `PROBLEM` через `problem_handoff`;
- сохранить human-in-the-loop: пользователь подтверждает, редактирует и сохраняет артефакты;
- обеспечить передачу результата в разработку, QA, архитектуру и Trello/backlog без потери контекста.

## 2. Фактическое состояние repo

Репозиторий содержит приложение `discovery-ai-agent`:

- frontend: React + Vite, `frontend/src`, API-клиент `frontend/src/api/client.ts`;
- backend: FastAPI, `backend/app/main.py`, API router `backend/app/api/discovery.py`;
- persistence: SQLAlchemy модели `DiscoveryProject`, `DiscoveryArtifact`, `LLMSettings`, локальная SQLite база `backend/data/discovery_agent.db`;
- agent runtime: `AgentOrchestrator`, `BaseAgent`, `AgentContext`, `AgentResult`;
- discovery agents: `ContextIngestionAgent`, `ProblemAgent`, `GoalAgent`, `BusinessEffectAgent`, `UseCaseAgent`, `RequirementsAgent`, `CriticAgent`;
- LLM clients: `MockLLMClient`, OpenRouter-compatible client, corporate-compatible client;
- context ingestion: upload/extraction для `txt`, `md`, `csv`, `docx`, `pdf`, `xlsx`, ограничение файла 15 МБ, chunks до 12 фрагментов по 3000 символов;
- export: DOCX export через `docx_export_service.py`;
- runtime docs: `docs/architecture/agent-runtime-contract.md`, `docs/architecture/ADR-001-agent-and-rag-framework-selection.md`.

Фактические ограничения MVP:

- авторизация и ролевая модель в API не реализованы;
- Trello-интеграция не реализована в коде, есть поле `jira_epic_url`;
- аудит изменений как отдельная сущность отсутствует;
- единый error envelope введен для основного MVP scope в рамках `BE-01-02`; остаются follow-up gaps по typed request schemas, upload file-level statuses и LLM settings hardening;
- Alembic migration `0001` не полностью отражает текущие ORM-поля `structured_content`, `rich_content_json`, `rendered_html`, которые добавляются на startup через schema patch;
- `source_trace`, `coverage`, `readiness`, `problem_handoff` существуют для анализа контекста, но не унифицированы для всех AI-артефактов.

## 3. Архитектурные компоненты

### 3.1 Frontend

Компонент: React/Vite SPA.

Ответственность:

- список проектов и карточки готовности;
- рабочая страница проекта с этапами Discovery;
- ручное редактирование и сохранение артефактов;
- загрузка источников контекста;
- запуск анализа контекста и генерации AI-артефактов;
- отображение LLM readiness, ошибок backend, статусов сохранения и индексации;
- страница LLM settings;
- запуск DOCX export.

Frontend должен использовать только публичный API backend через `VITE_API_URL` или `http://localhost:8000/api` по умолчанию.

### 3.2 Backend API

Компонент: FastAPI.

Ответственность:

- CRUD проектов;
- CRUD discovery-артефактов;
- загрузка и нормализация context sources;
- извлечение текста и chunking;
- запуск AI agents через `AgentOrchestrator`;
- проверка runtime/LLM readiness;
- расчет completion;
- генерация DOCX;
- хранение LLM settings без раскрытия API key в ответах.

### 3.3 Agent runtime

Текущий runtime состоит из:

- `AgentOrchestrator`: registry `artifact_type -> agent`;
- `BaseAgent`: общий контракт `build_prompt`, `_deterministic_result`, `run`, `run_with_result`;
- `AgentContext`: входной runtime-контекст агента;
- `AgentResult`: расширенный результат с `ok`, `content`, `structured_content`, `raw_llm_response`, `used_fallback`, `warnings`, `errors`, `source_trace`, `metadata`;
- специализированный путь `ContextIngestionAgent.analyze()` для JSON-контракта контекста.

Целевой runtime должен сохранить совместимость с текущими endpoint и расширить метаданные генерации: `trace_id`, `prompt_version`, `source_artifact_versions`, `llm_provider`, `llm_model`, `latency_ms`, `used_fallback`, `warnings`, `errors`.

### 3.4 Data storage

Текущая модель:

- `discovery_projects`;
- `discovery_artifacts`;
- `llm_settings`.

Целевое состояние должно отделить доменные данные от audit/runtime events и обеспечить миграции через Alembic без schema patch на startup.

### 3.5 Интеграции

Текущие интеграции:

- LLM provider: `mock`, `openrouter`, `corporate`;
- DOCX export;
- локальная загрузка файлов.

Целевые интеграции:

- Trello/backlog handoff;
- корпоративный LLM provider;
- опциональный внутренний retriever/RAG adapter;
- storage для исходных файлов, если требуется хранить оригиналы, а не только извлеченный текст.

## 4. Функциональные требования

| ID | Требование | Приоритет | Фактическое состояние |
|---|---|---:|---|
| FR-001 | Пользователь создает проект с названием, бизнес-доменом и ссылкой на внешнюю инициативу | Обязательно | Частично есть: `project_name`, `business_domain`, `jira_epic_url` |
| FR-002 | Пользователь видит список проектов и процент готовности Discovery | Обязательно | Есть через `GET /projects` и `/completion` |
| FR-003 | Пользователь открывает проект и работает по этапам Discovery | Обязательно | Есть в React `ProjectPage` |
| FR-004 | Пользователь сохраняет артефакт вручную как текст и структурированный JSON | Обязательно | Есть через `PUT /artifacts/{artifact_type}` |
| FR-005 | Система увеличивает версию артефакта при каждом сохранении | Обязательно | Есть в repository `upsert_artifact` |
| FR-006 | Пользователь загружает источники контекста | Обязательно | Есть для файлов через `/context/sources/upload` |
| FR-007 | Система извлекает текст, режет его на chunks и сохраняет метаданные источника | Обязательно | Есть для поддержанных форматов |
| FR-008 | Система анализирует контекст и формирует `extracted_knowledge` | Обязательно | Есть через `ContextIngestionAgent.analyze()` |
| FR-009 | Система формирует `source_trace`, `coverage`, `readiness`, `problem_handoff` | Обязательно | Есть для контекста |
| FR-010 | Система блокирует AI-генерацию, если LLM не готова | Обязательно | Есть через `_ensure_llm_ready` |
| FR-011 | Система генерирует артефакты Problem, Goal, Business Effect, Use Cases, Requirements, Final BT | Обязательно | Частично есть |
| FR-012 | Система поддерживает уточняющие вопросы и AI patch по этапам | Желательно | Есть через `/stage/{artifact_type}/questions`, `/ask`, `/apply-patch` |
| FR-013 | Система считает готовность по обязательным разделам | Обязательно | Есть |
| FR-014 | Система экспортирует БТ в DOCX | Обязательно | Есть |
| FR-015 | Система отмечает зависимые артефакты как stale после изменения upstream-этапа | Желательно | Частично реализовано на frontend |
| FR-016 | Система готовит handoff для Trello/backlog | Желательно | Требуется реализация |
| FR-017 | Система ведет audit trail действий пользователя и AI | Обязательно для production | Требуется реализация |
| FR-018 | Система поддерживает роли и права доступа | Обязательно для production | Требуется реализация |
| FR-019 | Система хранит историю knowledge snapshots | Желательно | Есть для context `knowledge_history`, до 30 записей |
| FR-020 | Система не подменяет пользовательское решение AI-результатом без явного сохранения/применения | Обязательно | Частично есть через ручное применение patch |

## 5. Нефункциональные требования

| ID | Категория | Требование |
|---|---|---|
| NFR-001 | Производительность | `GET /projects`, `GET /project`, `GET /artifacts`, `GET /completion` должны отвечать до 500 мс на локальной БД при типовой нагрузке MVP |
| NFR-002 | Производительность | Upload файла до 15 МБ должен завершаться без блокировки UI; для production требуется async/background job при больших документах |
| NFR-003 | LLM latency | LLM timeout должен управляться настройкой `timeout_seconds`; UI обязан показывать состояние ожидания |
| NFR-004 | Надежность | При ошибке LLM агент должен возвращать deterministic fallback или управляемую ошибку без потери пользовательского артефакта |
| NFR-005 | Совместимость | Существующие API route и типы `ProjectRead`, `ArtifactRead`, `CompletionResponse` должны сохранять backward compatibility до отдельного versioned API |
| NFR-006 | Наблюдаемость | Каждый AI-запуск должен иметь correlation/trace id, время выполнения, provider/model, статус и ошибку |
| NFR-007 | Локализация | Все user-facing сообщения, ошибки и документы должны быть на русском языке |
| NFR-008 | Доступность | Frontend должен корректно показывать недоступность backend и LLM |
| NFR-009 | Поддерживаемость | Все изменения схемы БД должны оформляться миграциями, а не только startup ALTER TABLE |
| NFR-010 | Экспорт | DOCX export должен быть воспроизводимым и включать версии/дату/статусы ключевых артефактов |

## 6. API requirements

### 6.1 Общие требования к API

- Базовый путь: `/api`.
- Все JSON endpoint должны возвращать `application/json`.
- Ошибки должны иметь единый формат:

```json
{
  "ok": false,
  "error": "ERROR_CODE",
  "human_message": "Сообщение для пользователя на русском языке",
  "details": {},
  "trace_id": "опционально"
}
```

- `404` должен использоваться для отсутствующих проектов и артефактов.
- `400` должен использоваться для ошибок валидации бизнес-операции: LLM не готова, контекст отсутствует, неподдерживаемый этап.
- `422` должен использоваться для Pydantic validation errors.
- `500` должен использоваться только для непредвиденных backend/runtime ошибок.

### 6.2 Текущие и целевые endpoint

| Endpoint | Метод | Назначение | Запрос | Ответ | Требования |
|---|---|---|---|---|---|
| `/health` | GET | Проверка backend | нет | `{status:"ok"}` | Не должен раскрывать настройки |
| `/api/runtime/status` | GET | Статус backend и LLM | нет | `backend`, `llm` | Не возвращать API key |
| `/api/projects` | GET | Список проектов | нет | `ProjectRead[]` | Сортировка по `created_at desc` допустима |
| `/api/projects` | POST | Создание проекта | `ProjectCreate` | `ProjectRead` | `project_name` обязателен |
| `/api/projects/{project_id}` | GET | Получение проекта | path `project_id` | `ProjectRead` | 404 если нет |
| `/api/projects/{project_id}` | PATCH | Обновление проекта | `ProjectUpdate` | `ProjectRead` | Валидировать статусы |
| `/api/projects/{project_id}` | DELETE | Удаление проекта | path | `{ok:true}` | Требуется audit event |
| `/api/projects/{project_id}/artifacts` | GET | Список артефактов | path | `ArtifactRead[]` | Не фильтрует по типу |
| `/api/projects/{project_id}/artifacts/{artifact_type}` | GET | Артефакт | path | `ArtifactRead` | Валидировать enum |
| `/api/projects/{project_id}/artifacts/{artifact_type}` | PUT | Upsert артефакта | `ArtifactWrite` | `ArtifactRead` | Увеличивать `version`, audit |
| `/api/projects/{project_id}/context/sources/upload` | POST | Загрузка источников | multipart `files[]` | `{ok,sources}` | Размер, формат, extraction status |
| `/api/projects/{project_id}/context/analyze` | POST | Анализ контекста | `context_input`, `documents`, `links` | `extracted_knowledge`, `source_trace`, `coverage`, `readiness`, `problem_handoff` | Требуется LLM readiness |
| `/api/projects/{project_id}/generate/{artifact_type}` | POST | Генерация артефакта | path | `ArtifactRead` | Не все `ArtifactType` имеют агента |
| `/api/projects/{project_id}/validate` | POST | Проверка CriticAgent | path | `ArtifactRead` | Сохраняет `VALIDATION_REPORT` |
| `/api/projects/{project_id}/problem/generate` | POST | Специализированная генерация проблемы | optional payload | `{ok,structured_content,version}` | Должна учитывать context handoff |
| `/api/projects/{project_id}/problem/ask` | POST | Уточнение проблемы | `message` | `patch`, `assistant_message` | Сейчас mock-like поведение |
| `/api/projects/{project_id}/problem/apply-patch` | POST | Применение patch проблемы | `patch`, `status` | `structured_content`, `version` | Нужна валидация полей |
| `/api/projects/{project_id}/goal/generate` | POST | Генерация целей | path | `{ok,warning,structured_content,draft,version}` | Учитывать CONTEXT и PROBLEM |
| `/api/projects/{project_id}/stage/{artifact_type}/questions` | POST | Генерация вопросов по этапу | path | `questions`, `structured_content` | Ограничить число вопросов |
| `/api/projects/{project_id}/stage/{artifact_type}/ask` | POST | Ответ на вопрос и AI patch | `message`, `question_id` | `patch`, `structured_content` | Сохранять `ai_answers` |
| `/api/projects/{project_id}/stage/{artifact_type}/apply-patch` | POST | Применение stage patch | `patch` | `structured_content` | Требуется audit |
| `/api/projects/{project_id}/completion` | GET | Готовность Discovery | path | `CompletionResponse` | Логика обязательных разделов должна быть документирована |
| `/api/projects/{project_id}/export/docx` | GET | DOCX export | path | binary DOCX | Content-Disposition с безопасным filename |
| `/api/settings/llm` | GET | Получение LLM settings | нет | masked settings | API key только masked/tail |
| `/api/settings/llm` | PUT | Сохранение LLM settings | provider/base_url/model/key/etc | masked settings | Не затирать key masked значением |
| `/api/settings/llm/test` | POST | Проверка LLM подключения | settings или saved | masked settings/status | Таймаут и error mapping |

### 6.3 API backward compatibility

- Нельзя переименовывать поля `id`, `project_name`, `business_domain`, `status`, `current_stage`, `jira_epic_url`, `artifact_type`, `content`, `structured_content`, `version` без versioned API.
- Новые поля в response должны быть optional для frontend.
- Error format можно унифицировать через добавление полей, но frontend должен продолжать понимать текущий `detail`.

## 7. Data model requirements

### 7.1 `DiscoveryProject`

| Поле | Тип | Обязательность | Правила |
|---|---|---|---|
| `id` | UUID/string | Да | Генерируется backend |
| `project_name` | string, 255 | Да | Не пустое, trim |
| `business_domain` | string, 255 | Нет | Бизнес-направление |
| `status` | enum | Да | `DRAFT`, `IN_PROGRESS`, `BT_READY`, `APPROVED` |
| `current_stage` | enum | Да | Текущий этап Discovery |
| `jira_epic_url` | string, 500 | Нет | Текущий generic external epic/link; для Trello нужна отдельная модель или переименование через migration |
| `created_at` | datetime | Да | UTC |
| `updated_at` | datetime | Да | UTC, обновляется при изменении |

### 7.2 `DiscoveryArtifact`

| Поле | Тип | Обязательность | Правила |
|---|---|---|---|
| `id` | UUID/string | Да | Генерируется backend |
| `project_id` | UUID/string | Да | FK на `discovery_projects`, cascade delete |
| `artifact_type` | enum | Да | См. список типов |
| `content` | text | Да | Человекочитаемый текст |
| `structured_content` | JSON | Нет | Структурированные поля этапа |
| `rich_content_json` | JSON | Нет | Rich editor model |
| `rendered_html` | text | Нет | Отображаемый HTML, требуется sanitization |
| `version` | integer | Да | Увеличивается на каждом upsert |
| `created_at` | datetime | Да | UTC |
| `updated_at` | datetime | Да | UTC |

Целевое ограничение: уникальность `(project_id, artifact_type)`.

### 7.3 Artifact types

Поддерживаемые типы:

- `CONTEXT`;
- `PROBLEM`;
- `GOAL`;
- `BUSINESS_EFFECT`;
- `AS_IS`;
- `TO_BE`;
- `USE_CASES`;
- `FUNCTIONAL_REQUIREMENTS`;
- `NON_FUNCTIONAL_REQUIREMENTS`;
- `RISKS`;
- `GLOSSARY`;
- `FINAL_BT`;
- `VALIDATION_REPORT`.

Обязательные для completion в текущей логике: `CONTEXT`, `PROBLEM`, `GOAL`, `BUSINESS_EFFECT`, `AS_IS`, `TO_BE`, `USE_CASES`, `FUNCTIONAL_REQUIREMENTS`, `RISKS`, `FINAL_BT`.

### 7.4 `LLMSettings`

| Поле | Тип | Обязательность | Правила |
|---|---|---|---|
| `id` | int | Да | Autoincrement |
| `provider` | string | Да | `mock`, `openrouter`, `corporate` |
| `base_url` | string | Нет | Не показывать приватные endpoints в публичной документации/логах |
| `api_key` | string | Нет | Не возвращать в открытом виде |
| `model` | string | Нет | Модель запроса |
| `timeout_seconds` | int | Да | Минимум/максимум должны быть валидированы |
| `temperature` | float | Да | Рекомендуемый диапазон 0-1 |
| `is_active` | bool | Да | Активная запись выбирается последней |
| `last_connection_status` | enum-like string | Нет | `mock`, `not_configured`, `connected`, `error`, `timeout`, `unauthorized`, `model_not_found`, `backend_error` |
| `last_latency_ms` | int | Нет | Последняя latency |
| `last_error` | string | Нет | Обрезать и не хранить secrets |
| `last_actual_model` | string | Нет | Модель из ответа provider |

### 7.5 Целевые новые сущности

Для production требуется добавить:

- `audit_events`: действия пользователя, AI-запуски, изменения артефактов, export;
- `agent_runs`: trace AI-запуска, prompt version, provider/model, latency, input artifact versions, result status;
- `context_sources`: отдельное хранение источников вместо вложенных массивов в `CONTEXT.structured_content`, если объем данных растет;
- `trello_links`: связь проекта/артефакта с Trello board/list/card/checklist.

## 8. Статусы и переходы

### 8.1 ProjectStatus

| Статус | Описание | Разрешенные переходы |
|---|---|---|
| `DRAFT` | Проект создан, Discovery не завершен | `IN_PROGRESS`, удаление |
| `IN_PROGRESS` | Идет заполнение и генерация артефактов | `BT_READY`, `DRAFT` при ручном откате |
| `BT_READY` | БТ готово к согласованию | `APPROVED`, `IN_PROGRESS` при доработке |
| `APPROVED` | БТ согласовано | `IN_PROGRESS` только через роль с правом reopen |

### 8.2 ProjectStage

Целевая последовательность:

`CONTEXT -> PROBLEM -> GOAL -> BUSINESS_EFFECT -> AS_IS -> TO_BE -> USE_CASES -> REQUIREMENTS -> RISKS -> FINAL_BT -> VALIDATION_REPORT`.

Правила:

- переход к `PROBLEM` должен учитывать `readiness.can_go_to_problem`;
- переход к downstream-этапу должен показывать предупреждение, если upstream-артефакт отсутствует или stale;
- изменение upstream-артефакта должно помечать downstream pipeline metadata как `stale`;
- `VALIDATION_REPORT` не должен считаться заменой ручного согласования.

### 8.3 Artifact pipeline status

В `structured_content.pipeline_meta.status` целево использовать:

- `empty`;
- `draft`;
- `manually_edited`;
- `ai_generated`;
- `ready`;
- `stale`;
- `error`.

## 9. Security requirements

| ID | Требование |
|---|---|
| SEC-001 | API key LLM provider не должен возвращаться frontend в открытом виде; допустимы masked value и `key_tail` |
| SEC-002 | Логи не должны содержать API key, токены, credentials, приватные endpoints, полные prompt с закрытыми данными без redaction |
| SEC-003 | `rendered_html` должен проходить sanitization перед отображением, если сохраняется HTML |
| SEC-004 | Upload должен ограничивать размер, типы файлов и обрабатывать ошибки парсинга без stack trace для пользователя |
| SEC-005 | DOCX export filename должен быть безопасным и не допускать path traversal |
| SEC-006 | Для production требуется authn/authz: минимум роли `Admin`, `Analyst`, `Reviewer`, `Viewer` |
| SEC-007 | Изменение LLM settings разрешено только `Admin` |
| SEC-008 | Удаление проекта разрешено только владельцу или `Admin` и должно аудитироваться |
| SEC-009 | Внешние LLM вызовы должны быть явно помечены как передача данных внешнему provider |
| SEC-010 | Для corporate режима должен быть allowlist provider/base_url и запрет произвольных внешних endpoints без approval |

## 10. LLM/RAG requirements

### 10.1 LLM runtime

- Поддержать provider modes: `mock`, `openrouter`, `corporate`.
- Перед генерацией проверять `ready_for_generation`.
- Для каждого AI-запуска сохранять:
  - `agent_name`;
  - `artifact_type`;
  - `project_id`;
  - `input_artifact_versions`;
  - `prompt_version`;
  - `provider`;
  - `model`;
  - `actual_model`;
  - `temperature`;
  - `timeout_seconds`;
  - `latency_ms`;
  - `used_fallback`;
  - `warnings`;
  - `errors`;
  - `source_trace`;
  - `created_at`.
- AI output должен быть на русском языке.
- Для JSON-контрактов backend обязан валидировать и нормализовать ответ LLM.
- При невалидном JSON должен использоваться fallback или управляемая ошибка.

### 10.2 Анализ контекста

Текущий контракт `ContextIngestionAgent.analyze()` должен быть сохранен:

- `extracted_knowledge`;
- `source_trace`;
- `coverage`;
- `readiness`;
- `overview_for_ai`;
- `problem_handoff`;
- `indexing_status`;
- `analyzed_at`.

Требования:

- не генерировать TO-BE, solution, requirements и final BT на этапе контекста;
- не изобретать факты без источников;
- источники только с метаданными должны попадать в missing information;
- `source_trace.used=false` должен объяснять причину;
- readiness score должен быть воспроизводимым по coverage weights.

### 10.3 RAG и поиск по фрагментам

Целевое развитие:

- сначала внутренний `SimpleRetriever` поверх уже извлеченных chunks;
- retrieval должен возвращать top-k chunks, source id, source name, order, score, metadata;
- RAG adapter должен быть отключаемым;
- внешние frameworks допускаются только после отдельного ADR/license gate;
- retrieval не должен заменять source_trace, а должен обогащать его.

## 11. Trello integration requirements

Фактическое состояние: Trello-интеграции в коде нет. В проекте есть только поле `jira_epic_url`, которое сейчас играет роль внешней ссылки.

Целевое назначение Trello:

- создавать или обновлять карточку Discovery/Delivery по утвержденному БТ;
- прикладывать summary, acceptance criteria, API/data/status/error sections;
- создавать checklist по delivery phases;
- сохранять обратную ссылку на Trello card в проекте;
- не выполнять write-операции без явного действия пользователя и approval.

Минимальные требования к модели связи:

- `trello_board_id`;
- `trello_list_id`;
- `trello_card_id`;
- `trello_card_url`;
- `sync_status`: `not_linked`, `draft_ready`, `sync_pending`, `synced`, `sync_error`;
- `last_synced_at`;
- `last_sync_error`.

Требования к безопасности:

- Trello token/API key не хранить в артефактах Discovery;
- все Trello write операции аудитировать;
- при ошибке Trello не терять локальные Discovery-данные;
- повторная синхронизация должна быть идемпотентной по `trello_card_id`.

## 12. Logging и audit requirements

### 12.1 Application logging

Логировать:

- startup backend;
- health/runtime status errors;
- upload/extraction status;
- AI generation start/end/error;
- DOCX export;
- LLM test status без secrets;
- unexpected exceptions с trace id.

Не логировать:

- API keys;
- полные credentials;
- приватные endpoints;
- полные документы пользователя без redaction policy.

### 12.2 Audit events

Целевая сущность `audit_events` должна фиксировать:

- `event_id`;
- `event_name`;
- `actor_id` или `system`;
- `project_id`;
- `artifact_id`;
- `artifact_type`;
- `action`;
- `before_version`;
- `after_version`;
- `result`: `success` или `error`;
- `error_code`;
- `trace_id`;
- `created_at`.

Базовые события:

- `project.created`;
- `project.updated`;
- `project.deleted`;
- `artifact.saved`;
- `artifact.generated`;
- `artifact.patch_applied`;
- `context.source_uploaded`;
- `context.analyzed`;
- `llm.settings_updated`;
- `llm.connection_tested`;
- `docx.exported`;
- `trello.sync_requested`;
- `trello.sync_completed`;
- `trello.sync_failed`.

## 13. Error handling

| Code | HTTP | Условие | Сообщение пользователю | Retry |
|---|---:|---|---|---|
| `PROJECT_NOT_FOUND` | 404 | Проект не найден | Проект не найден | Нет |
| `ARTIFACT_NOT_FOUND` | 404 | Артефакт не найден | Артефакт не найден | Нет |
| `UNSUPPORTED_ARTIFACT_TYPE` | 400 | Для типа нет агента/операции | Генерация для этого раздела не поддерживается | Нет |
| `LLM_NOT_READY` | 400 | LLM не настроена или не подключена | LLM не настроена. Откройте настройки и проверьте подключение | Да, после настройки |
| `LLM_TIMEOUT` | 400/504 | Timeout provider | Превышено время ожидания ответа LLM | Да |
| `LLM_UNAUTHORIZED` | 400/401 | Provider вернул 401/403 | Ошибка авторизации LLM. Проверьте API key | Да, после настройки |
| `LLM_MODEL_NOT_FOUND` | 400 | Модель недоступна | Модель недоступна или указана неверно | Да, после настройки |
| `LLM_INVALID_JSON` | 400 | JSON-контракт не распарсен | AI вернул неструктурированный ответ | Да |
| `FILE_TOO_LARGE` | 400 | Файл больше 15 МБ | Файл слишком большой. Максимальный размер: 15 МБ | Да, другой файл |
| `UNSUPPORTED_FILE_TYPE` | 400 | Расширение не поддержано | Неподдерживаемый формат файла | Да, другой формат |
| `TEXT_EXTRACTION_FAILED` | 400 | Ошибка парсинга файла | Не удалось извлечь текст из файла | Да |
| `DOCX_EXPORT_FAILED` | 500 | Ошибка экспорта | Не удалось сформировать DOCX | Да |
| `TRELLO_SYNC_FAILED` | 502 | Ошибка Trello API | Не удалось синхронизировать карточку Trello | Да |

## 14. Критерии приемки

### 14.1 System acceptance

- Создание проекта сохраняет `DRAFT` и `CONTEXT` по умолчанию.
- Пользователь может загрузить поддержанный файл до 15 МБ и увидеть extraction status.
- После анализа контекста сохраняются `extracted_knowledge`, `source_trace`, `coverage`, `readiness`, `problem_handoff`.
- Если LLM не готова, генерация не запускается и пользователь получает понятное сообщение.
- Пользователь может сгенерировать и вручную отредактировать ключевые артефакты.
- Версия артефакта увеличивается при каждом сохранении.
- Completion корректно считает обязательные разделы.
- DOCX export содержит ключевые разделы БТ.
- API key никогда не возвращается frontend в открытом виде.
- Все user-facing сообщения в новых/целевых сценариях на русском языке.

### 14.2 Критерии готовности к production

- Есть authn/authz и роли.
- Есть audit trail.
- Есть единый error envelope.
- Есть миграции для всех фактических полей БД.
- Есть trace id для AI generation и upload/analyze/export.
- Есть тесты API, agent runtime, content extraction, UI critical path.
- Trello write операции выполняются только после явного подтверждения.

## 15. Тестовые сценарии

### 15.1 Позитивные сценарии

| ID | Сценарий | Ожидаемый результат |
|---|---|---|
| TC-001 | Создать проект с названием и доменом | Возвращен `ProjectRead`, статус `DRAFT`, stage `CONTEXT` |
| TC-002 | Сохранить `CONTEXT` вручную | Создан `DiscoveryArtifact`, version `1` |
| TC-003 | Повторно сохранить `CONTEXT` | Version увеличился на `1` |
| TC-004 | Загрузить `docx` до 15 МБ | Source status `ready` или `empty/failed` с причиной |
| TC-005 | Запустить context analyze при ready LLM | Сохранен context snapshot, `indexing_status=completed` |
| TC-006 | Сгенерировать Problem после контекста | Создан/обновлен `PROBLEM`, сохранен structured draft |
| TC-007 | Ответить на уточняющий вопрос | Ответ сохранен в `ai_answers`, сформирован patch |
| TC-008 | Применить stage patch | `structured_content` обновлен |
| TC-009 | Получить completion | Response содержит процент и missing sections |
| TC-010 | Экспортировать DOCX | Ответ binary DOCX с корректным media type |
| TC-011 | Проверить LLM в mock mode | Статус `mock`, generation разрешена |

### 15.2 Негативные и граничные сценарии

| ID | Сценарий | Ожидаемый результат |
|---|---|---|
| TC-101 | Получить несуществующий проект | 404 `PROJECT_NOT_FOUND` |
| TC-102 | Запустить генерацию при неготовой LLM | 400 `LLM_NOT_READY` |
| TC-103 | Загрузить файл больше 15 МБ | Source status `error`, код `FILE_TOO_LARGE` |
| TC-104 | Загрузить неподдержанный формат | Source status `unsupported` |
| TC-105 | LLM возвращает пустой текст в `run_with_result` | Используется deterministic fallback |
| TC-106 | LLM возвращает невалидный JSON для context analyze | Управляемая ошибка или fallback без порчи старого контекста |
| TC-107 | Изменить upstream artifact после downstream generation | Downstream pipeline status `stale` |
| TC-108 | Сохранить masked API key | Старый ключ не должен быть затерт masked строкой |
| TC-109 | Ошибка DOCX export | Пользователь получает управляемую ошибку без stack trace |
| TC-110 | Trello API timeout | Локальные данные сохранены, sync status `sync_error` |

### 15.3 State transition сценарии

| ID | Объект | Переход | Ожидаемый результат |
|---|---|---|---|
| ST-001 | Project | `DRAFT -> IN_PROGRESS` | Разрешено при начале заполнения |
| ST-002 | Project | `IN_PROGRESS -> BT_READY` | Разрешено при completion обязательных разделов и validation report |
| ST-003 | Project | `BT_READY -> APPROVED` | Разрешено reviewer/admin после согласования |
| ST-004 | Project | `APPROVED -> IN_PROGRESS` | Разрешено только с правом reopen и audit reason |
| ST-005 | Context readiness | `blocked -> warning` | Появился ручной контекст или документ |
| ST-006 | Context readiness | `warning -> ready` | Покрыты процессы и системы, score >= 70 |
| ST-007 | Artifact pipeline | `ready -> stale` | Изменился upstream artifact |
| ST-008 | Trello sync | `draft_ready -> synced` | Card создана/обновлена успешно |
| ST-009 | Trello sync | `sync_pending -> sync_error` | Trello вернул ошибку или timeout |

## 16. Фазы поставки

### Фаза 1. Стабилизация текущего MVP

- Зафиксировать фактический OpenAPI/error contract.
- Унифицировать error envelope.
- Привести Alembic migrations к текущим ORM-полям.
- Добавить уникальность `(project_id, artifact_type)`.
- Покрыть API smoke tests.

### Фаза 2. Укрепление agent runtime

- Расширить `AgentResult` metadata и сохранять `agent_runs`.
- Добавить trace id и prompt version.
- Унифицировать fallback/error policy.
- Распространить `source_trace` и input artifact versions на downstream agents.

### Фаза 3. Слой контекста и RAG

- Вынести context sources в отдельную модель при необходимости.
- Добавить `SimpleRetriever` поверх chunks.
- Добавить top-k retrieval trace.
- Подготовить adapter boundary для внешних RAG frameworks без подключения их в ядро.

### Фаза 4. Безопасность и аудит

- Ввести authn/authz.
- Ввести audit events.
- Добавить redaction логов и prompt/runtime metadata.
- Ограничить LLM provider/base_url allowlist для corporate режима.

### Фаза 5. Интеграция Trello/backlog

- Добавить модель Trello link/sync status.
- Подготовить draft payload для карточки.
- Реализовать idempotent sync с явным подтверждением пользователя.
- Логировать и аудитировать sync операции.

### Фаза 6. Экспорт и handoff

- Расширить DOCX: версии артефактов, source trace summary, validation report, open questions.
- Подготовить handoff templates для architect, backend, frontend, database, QA, LLM/RAG, security.
- Добавить release readiness checklist.

## 17. Допущения

- Система развивается из локального MVP в production-ready платформу без замены React/FastAPI основы.
- SQLite допустим для MVP, но production может потребовать PostgreSQL и полноценные миграции.
- `jira_epic_url` в текущей модели является legacy/generic external link, а Trello потребует отдельной связи.
- Внешние AI/RAG dependencies добавляются только после отдельного архитектурного и license review.
- Все новые пользовательские тексты и документы должны быть на русском языке.

## 18. Открытые вопросы

- Какая production модель пользователей и организаций требуется: single workspace или multi-tenant?
- Нужно ли хранить оригиналы загруженных файлов или достаточно extracted text/chunks?
- Нужен ли PostgreSQL как целевая БД на ближайшем этапе?
- Какие Trello board/list/status conventions должны использоваться?
- Какие корпоративные LLM endpoints разрешены и кто утверждает allowlist?
- Нужен ли полноценный approval workflow для `BT_READY -> APPROVED`?
- Какие сроки retention для audit events, agent runs и uploaded context?

## 19. Риски

- Без auth/audit система не готова к production и работе с чувствительными Discovery-данными.
- Без единого error envelope frontend будет продолжать обрабатывать ошибки неоднородно.
- Startup schema patch вместо миграций повышает риск расхождения окружений.
- Передача контекста во внешний LLM provider может нарушать корпоративные ограничения, если нет явного режима согласия и allowlist.
- Trello sync без идемпотентности может создавать дубли карточек.
- `rendered_html` без sanitization может создать XSS-риск.

## 20. Handoff

> Уточнение слоев: Product AI Agents и Global Codex Delivery Agents - разные слои. Product AI Agents работают внутри backend/runtime AI Discovery Platform для пользователей продукта. Handoff ниже относится к глобальным Codex delivery agents, которые помогают разрабатывать платформу через Codex.

От: `ai-system-analyst`  
Кому: `ai-solution-architect`, `ai-backend-developer`, `ai-frontend-developer`, `ai-database-engineer`, `ai-llm-rag-engineer`, `ai-security-reviewer`, `ai-qa-engineer`, `ai-test-automation-engineer`, `ai-trello-analyst`

Передаваемые артефакты:

- системное ТЗ: `docs/system/tz-ai-discovery-platform-target.md`;
- runtime contract: `docs/architecture/agent-runtime-contract.md`;
- ADR по AI/RAG framework: `docs/architecture/ADR-001-agent-and-rag-framework-selection.md`;
- фактические API/модели в `discovery-ai-agent/backend/app`;
- фактический frontend API usage в `discovery-ai-agent/frontend/src`.

Запрашиваемые действия:

- архитектору: подтвердить target architecture, boundaries, rollout/rollback и ADR для production;
- backend: спроектировать API/error/audit/agent_runs реализацию;
- frontend: синхронизировать UI states с целевыми status/error contracts;
- database: подготовить миграции и constraints;
- LLM/RAG: описать prompt/retrieval contracts и eval criteria;
- security: провести auth/secrets/upload/HTML/LLM provider review;
- QA/test automation: подготовить manual и automated test suites по сценариям выше;
- Trello analyst: подготовить карточки/labels/checklists без прямой записи в Trello до approval.

Критерий качества:

- документ пригоден для разработки только после ответа на open questions, подтверждения security boundary и согласования delivery phases.
