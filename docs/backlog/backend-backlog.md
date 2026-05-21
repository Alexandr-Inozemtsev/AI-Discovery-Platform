# Backend backlog FastAPI

## Контекст ревизии

Ревизия проведена по `discovery-ai-agent/backend`: FastAPI приложение, API слой `app/api/discovery.py`, модели и репозитории `app/models`, `app/repositories`, agent runtime `app/agents`, LLM клиенты `app/llm`, сервисы `app/services`, миграции Alembic и backend tests.

Ограничения ревизии:
- production-код не изменялся;
- backlog описывает backend-работы для включения в общий backlog;
- приоритеты: `P0` критично для MVP, `P1` важно для MMP, `P2` целевой контур;
- этапы: `MVP`, `MMP`, `Целевой контур`.

## EPIC-BE-01. Контракт и декомпозиция FastAPI endpoint-ов

**Название:** Стабилизировать backend API discovery workflow.

**Описание:** Сейчас один модуль `app/api/discovery.py` содержит CRUD проектов, CRUD артефактов, context upload/analyze, генерацию stages, problem/goal flows, completion, DOCX export, runtime status и LLM settings. Нужно формализовать API contracts, выровнять валидацию, статусы ошибок и response shape, а затем декомпозировать роуты по зонам ответственности без изменения пользовательского workflow.

**Приоритет:** P0

**Этап:** MVP

**Зависимости:** system API contract, frontend consumers, QA smoke сценарии, security review по auth/authz.

**Labels:** `backend`, `fastapi`, `api-contract`, `validation`, `errors`, `mvp`

### BE-01-01. Описать и зафиксировать OpenAPI contracts для текущих endpoint-ов

**Статус:** Done

**Документ:** `docs/api/openapi-contracts-current.md`

**Описание:** Зафиксировать контракт текущих endpoint-ов: `/health`, `/api/runtime/status`, `/api/projects`, `/api/projects/{project_id}`, `/api/projects/{project_id}/artifacts`, `/api/projects/{project_id}/context/sources/upload`, `/api/projects/{project_id}/context/analyze`, `/api/projects/{project_id}/generate/{artifact_type}`, `/api/projects/{project_id}/validate`, `/api/projects/{project_id}/problem/*`, `/api/projects/{project_id}/goal/generate`, `/api/projects/{project_id}/stage/{artifact_type}/*`, `/api/projects/{project_id}/completion`, `/api/projects/{project_id}/export/docx`, `/api/settings/llm`.

**Приоритет:** P0

**Этап:** MVP

**Зависимости:** актуальные frontend calls, `app/schemas/discovery.py`, `ArtifactType`, `ProjectStatus`, `ProjectStage`.

**Критерии приемки:**
- Для каждого endpoint-а описаны method, path, request body/query/path params, success response, error response.
- Контракт покрывает русские пользовательские ошибки и машинные поля `ok`, `error`, `details`, где они используются.
- Контракт явно фиксирует enum-значения artifact/project stage/status.

**DoD:** Контракт доступен в backend docs или OpenAPI schema; QA и frontend могут использовать его как источник истины; не осталось endpoint-ов без описанного response shape.

**Labels:** `backend`, `openapi`, `api-contract`, `mvp`

### BE-01-02. Ввести единый формат backend ошибок

**Описание:** Сейчас ошибки возвращаются как строки `HTTPException`, dict payloads и разные поля LLM ошибок. Нужно унифицировать формат ошибок для validation, not found, LLM not ready, LLM provider errors, extraction errors и backend errors.

**Приоритет:** P0

**Этап:** MVP

**Зависимости:** API contract, frontend error handling, QA regression.

**Критерии приемки:**
- Все новые и измененные endpoint-ы возвращают единый error envelope.
- Для `404`, `400`, `500` заданы стабильные `error_code`, `human_message`, `details`.
- LLM ошибки не раскрывают API key, приватные headers или полный закрытый endpoint.

**DoD:** Добавлены backend tests на основные error paths; frontend не ломается на текущих сценариях; секреты маскируются.

**Labels:** `backend`, `errors`, `security`, `validation`, `mvp`

### BE-01-03. Разнести discovery API по роутерам

**Описание:** Разделить текущий монолитный API слой на роутеры: projects, artifacts, context, generation, stage assistance, export, settings/runtime. Цель - снизить риск регрессий и упростить дальнейшее развитие.

**Приоритет:** P1

**Этап:** MMP

**Зависимости:** BE-01-01, backend tests, frontend smoke.

**Критерии приемки:**
- Paths остаются обратно совместимыми.
- `app/api/discovery.py` больше не содержит все зоны ответственности в одном файле.
- Shared helpers вынесены в отдельные backend modules без циклических импортов.

**DoD:** Все существующие backend tests проходят; добавлен smoke test на регистрацию роутеров; OpenAPI содержит прежние paths.

**Labels:** `backend`, `fastapi`, `refactoring`, `mmp`

### BE-01-04. Усилить Pydantic validation для request payloads

**Описание:** Часть endpoint-ов принимает `dict`, включая context analyze, problem/ask/apply-patch, stage ask/apply-patch, LLM settings/test. Нужно заменить неструктурированные payloads на Pydantic схемы с явными nullable/default rules.

**Приоритет:** P0

**Этап:** MVP

**Зависимости:** API contract, frontend payload inventory.

**Критерии приемки:**
- Для публичных request body есть Pydantic модели.
- Некорректные поля и типы возвращают понятные validation errors.
- Backward compatibility сохранена для текущих frontend payloads.

**DoD:** Добавлены tests на valid/invalid payloads; схемы доступны в OpenAPI; ручные dict accesses минимизированы.

**Labels:** `backend`, `pydantic`, `validation`, `mvp`

## EPIC-BE-02. Agent runtime и генерация артефактов

**Название:** Сделать agent runtime управляемым, наблюдаемым и расширяемым.

**Описание:** Текущий runtime включает `BaseAgent`, `AgentContext`, `AgentResult`, deterministic fallback и `AgentOrchestrator`. Генерация частично идет через generic `/generate/{artifact_type}`, частично через специализированные `/problem/generate`, `/goal/generate`, `/stage/*`. Нужно выровнять contract выполнения, traceability, fallback behavior, source context linking и ошибки.

**Приоритет:** P0

**Этап:** MVP

**Зависимости:** LLM settings, artifact storage, context readiness, QA сценарии генерации.

**Labels:** `backend`, `agents`, `runtime`, `llm`, `mvp`

### BE-02-01. Зафиксировать единый AgentResult contract для всех генераторов

**Описание:** Сейчас `BaseAgent.run_with_result` возвращает `AgentResult`, но специализированные генераторы в API формируют собственные dict responses. Нужно привести генерацию CONTEXT/PROBLEM/GOAL/STAGE к единому runtime result contract.

**Приоритет:** P0

**Этап:** MVP

**Зависимости:** BE-01-01, `AgentResult`, frontend expectations.

**Критерии приемки:**
- Ответы генерации содержат стабильные поля: `ok`, `artifact_type`, `content`, `structured_content`, `version`, `used_fallback`, `warnings`, `errors`, `source_trace`, `metadata`.
- Fallback явно отражается в ответе и сохраняется в metadata.
- Ошибки LLM и пустые ответы различимы.

**DoD:** Tests покрывают success, provider error, empty response, deterministic fallback; contract documented.

**Labels:** `backend`, `agents`, `contract`, `mvp`

### BE-02-02. Синхронизировать generic и stage-specific генерацию

**Описание:** Generic `/generate/{artifact_type}` и специализированные `/problem/generate`, `/goal/generate`, `/stage/{artifact_type}/*` имеют разные правила контекста, версионирования и response shape. Нужно определить, какие flows остаются canonical, а какие становятся compatibility endpoints.

**Приоритет:** P1

**Этап:** MMP

**Зависимости:** product workflow decision, frontend routing, QA regression.

**Критерии приемки:**
- Для каждого artifact type определен canonical generator.
- Дублирующая логика prompt/parse/save вынесена в service layer.
- Compatibility endpoints сохраняют прежние paths или имеют migration plan.

**DoD:** Backend tests покрывают canonical flow для CONTEXT, PROBLEM, GOAL, FUNCTIONAL_REQUIREMENTS; frontend smoke подтвержден.

**Labels:** `backend`, `agents`, `service-layer`, `mmp`

### BE-02-03. Добавить runtime telemetry для agent runs

**Описание:** Нужны trace id, latency, provider/model, prompt size, response size, fallback flag и warning/error metadata без сохранения секретов и полного чувствительного контента.

**Приоритет:** P1

**Этап:** MMP

**Зависимости:** observability policy, security reviewer, LLM settings.

**Критерии приемки:**
- Каждый agent run получает trace id.
- В логах и metadata есть latency, artifact type, provider, model, status.
- API key, bearer token и приватные payload fragments не логируются.

**DoD:** Добавлены tests на metadata; проведена проверка отсутствия secrets в logs/errors; runtime status может использовать агрегированные данные.

**Labels:** `backend`, `observability`, `agents`, `security`, `mmp`

### BE-02-04. Расширить orchestrator registry для всех ArtifactType

**Описание:** `AgentOrchestrator` покрывает не все значения `ArtifactType` и переиспользует `RequirementsAgent` для нескольких типов. Нужно явно описать поддержку, fallback и ошибки для неподдержанных типов.

**Приоритет:** P1

**Этап:** MMP

**Зависимости:** product scope по stages, system analyst по artifact taxonomy.

**Критерии приемки:**
- Для каждого `ArtifactType` задано состояние: supported, planned, unsupported.
- Unsupported artifact generation возвращает стабильную ошибку.
- Registry не допускает silent no-op.

**DoD:** Tests покрывают supported/unsupported types; docs обновлены; OpenAPI отражает допустимые enum.

**Labels:** `backend`, `agents`, `artifact-types`, `mmp`

## EPIC-BE-03. Context upload и extraction pipeline

**Название:** Надежная загрузка, извлечение и индексация контекста.

**Описание:** Текущий backend поддерживает upload `txt`, `md`, `csv`, `docx`, `pdf`, `xlsx`, частично `xls` как unsupported, лимит 15 МБ, извлечение текста и chunks. Context analyze сохраняет `extracted_knowledge`, `source_trace`, `coverage`, `readiness`, `problem_handoff`, `knowledge_history`. Нужно стабилизировать pipeline, статусы и повторную обработку.

**Приоритет:** P0

**Этап:** MVP

**Зависимости:** frontend upload UX, storage/versioning, LLM readiness, QA fixtures.

**Labels:** `backend`, `context`, `upload`, `extraction`, `mvp`

### BE-03-01. Уточнить матрицу поддерживаемых форматов и статусов extraction

**Описание:** В API `SUPPORTED_CONTEXT_EXTENSIONS` включает `xls`, но service возвращает `xls` как unsupported. Нужно зафиксировать ожидаемое поведение по форматам, MIME, статусам `completed`, `empty`, `unsupported`, `failed`.

**Приоритет:** P0

**Этап:** MVP

**Зависимости:** frontend validation, QA file fixtures.

**Критерии приемки:**
- Для каждого формата описан outcome и пользовательское сообщение.
- API и extraction service используют согласованную матрицу.
- `xls` явно помечен как unsupported с рекомендацией конвертации.

**DoD:** Tests покрывают txt/md/csv/docx/pdf/xlsx/xls/unsupported/empty/oversize; contract documented.

**Labels:** `backend`, `context`, `validation`, `mvp`

### BE-03-02. Добавить идемпотентность и dedup для context sources

**Описание:** Upload добавляет источники в `documents/uploaded_files` без dedup. Нужно определить ключи уникальности и поведение повторной загрузки.

**Приоритет:** P1

**Этап:** MMP

**Зависимости:** artifact storage, frontend source management.

**Критерии приемки:**
- Повторная загрузка того же файла не создает неконтролируемые дубликаты.
- Источник имеет стабильные metadata: filename, size, hash или source fingerprint, uploaded_at.
- Можно обновить источник и перевести context `indexing_status` в `requires_update`.

**DoD:** Tests покрывают повторную загрузку, обновление и mixed batch; source trace сохраняет связь с source id.

**Labels:** `backend`, `context`, `idempotency`, `mmp`

### BE-03-03. Ввести отдельный service layer для context ingestion

**Описание:** Upload, normalization, merge structured content, history trimming и analyze orchestration сейчас находятся в API module. Нужно вынести pipeline в сервисы с чистыми входами/выходами.

**Приоритет:** P1

**Этап:** MMP

**Зависимости:** BE-01-03, BE-03-01.

**Критерии приемки:**
- API endpoint содержит request/response mapping, а бизнес-логика находится в context service.
- Service покрыт unit tests без FastAPI dependency wiring.
- Ошибки extraction и analyze мапятся в единый error envelope.

**DoD:** Existing behavior сохранен; tests покрывают service-level merge, status transitions, history limit.

**Labels:** `backend`, `context`, `service-layer`, `mmp`

### BE-03-04. Подготовить async/offline extraction для больших файлов

**Описание:** Извлечение сейчас выполняется синхронно в request lifecycle. Для целевого контура нужна очередь/фоновые задачи, progress status и retry.

**Приоритет:** P2

**Этап:** Целевой контур

**Зависимости:** DevOps runtime, storage design, observability.

**Критерии приемки:**
- Upload быстро возвращает source ids и статус обработки.
- Extraction выполняется асинхронно с progress/retry/error state.
- Есть endpoint для получения статуса источников и результатов chunks.

**DoD:** Load/performance smoke для больших файлов; retry policy documented; failures не блокируют весь project context.

**Labels:** `backend`, `context`, `async`, `target`

## EPIC-BE-04. Artifact storage и versioning

**Название:** Управляемое хранение артефактов, версий и rich content.

**Описание:** `DiscoveryArtifact` хранит `content`, `structured_content`, `rich_content_json`, `rendered_html`, `version`; `upsert_artifact` увеличивает version при каждом сохранении, но нет отдельной таблицы snapshots и нет constraints уникальности `project_id + artifact_type`. Для PROBLEM и CONTEXT частичная история хранится внутри JSON. Нужно усилить consistency, версионирование и rollback/read APIs.

**Приоритет:** P0

**Этап:** MVP

**Зависимости:** database engineer, migration plan, frontend artifact editor, DOCX export.

**Labels:** `backend`, `artifacts`, `versioning`, `storage`, `mvp`

### BE-04-01. Добавить уникальность artifact per project/type

**Описание:** Repository предполагает один artifact на `project_id + artifact_type`, но модель и миграция не фиксируют это constraint. Нужно добавить DB-level constraint и обработку конфликтов.

**Приоритет:** P0

**Этап:** MVP

**Зависимости:** database migration, data cleanup/backfill.

**Критерии приемки:**
- В DB невозможно создать два активных artifact одного типа в одном проекте.
- Repository корректно работает при race condition.
- Ошибка конфликта мапится в стабильный backend error.

**DoD:** Alembic migration, repository tests, проверка существующих данных перед constraint.

**Labels:** `backend`, `database`, `artifacts`, `mvp`

### BE-04-02. Спроектировать историю версий артефактов

**Описание:** Текущий `version` является счетчиком последнего состояния; snapshots частично лежат в JSON отдельных flows. Нужна единая история: кто/что/когда изменил, diff или snapshot, source agent run, source context version.

**Приоритет:** P1

**Этап:** MMP

**Зависимости:** database engineer, agent runtime telemetry, security/privacy policy.

**Критерии приемки:**
- Для каждого сохранения можно получить предыдущие версии.
- Версия содержит metadata: created_at, source, source_context_version, agent_run_id, change reason.
- Есть API для list/get artifact versions.

**DoD:** Migration и repository API готовы; tests покрывают create/update/list/get version; frontend получает read contract.

**Labels:** `backend`, `versioning`, `audit`, `mmp`

### BE-04-03. Нормализовать structured_content contracts по artifact types

**Описание:** `structured_content` используется разными flows без единой схемы. Нужно описать и валидировать минимальные contracts для CONTEXT, PROBLEM, GOAL, stage artifacts.

**Приоритет:** P1

**Этап:** MMP

**Зависимости:** system analyst artifact schema, frontend forms, QA fixtures.

**Критерии приемки:**
- Для ключевых artifact types есть Pydantic схемы structured content.
- Save API валидирует обязательные поля и сохраняет backward-compatible extras при необходимости.
- DOCX export и completion используют схемы, а не неявные dict keys.

**DoD:** Tests на serialization/deserialization; schema docs обновлены; некорректный structured content не ломает export.

**Labels:** `backend`, `artifacts`, `schema`, `validation`, `mmp`

### BE-04-04. Разделить plain content, rich content и rendered HTML lifecycle

**Описание:** `content`, `rich_content_json`, `rendered_html` сохраняются вместе, но нет правил, что является source of truth. Нужно определить lifecycle и валидацию для editor/export flows.

**Приоритет:** P2

**Этап:** Целевой контур

**Зависимости:** frontend editor model, technical writer/export requirements.

**Критерии приемки:**
- Для каждого artifact type определен source of truth.
- Rendered HTML можно пересоздать из rich content или явно пометить stale.
- Plain content синхронизируется с rich content по понятным правилам.

**DoD:** Backend service обновлен; tests покрывают stale/render sync; DOCX export использует корректный источник.

**Labels:** `backend`, `artifacts`, `rich-content`, `target`

## EPIC-BE-05. DOCX export

**Название:** Production-ready экспорт Discovery артефактов в DOCX.

**Описание:** `build_docx` формирует документ через `python-docx`, использует фиксированный `SECTION_ORDER`, plain content для большинства разделов и специальную обработку GOAL. Нужно улучшить шаблон, полноту данных, устойчивость к structured content и версионирование экспорта.

**Приоритет:** P1

**Этап:** MMP

**Зависимости:** artifact schemas, business template, QA export checks, technical writer.

**Labels:** `backend`, `docx`, `export`, `mmp`

### BE-05-01. Зафиксировать DOCX template contract

**Описание:** Описать состав разделов, порядок, заголовки, поля проекта, версию, автора, даты, обязательность разделов и поведение для пустых артефактов.

**Приоритет:** P1

**Этап:** MMP

**Зависимости:** business analyst, technical writer, artifact taxonomy.

**Критерии приемки:**
- Template contract согласован для CONTEXT, PROBLEM, GOAL, BUSINESS_EFFECT, AS_IS, TO_BE, USE_CASES, REQUIREMENTS, RISKS, FINAL_BT.
- Пустые разделы получают единый placeholder.
- Filename и metadata документа определены.

**DoD:** Contract documented; QA имеет эталонный expected structure; export endpoint не меняет path.

**Labels:** `backend`, `docx`, `template`, `mmp`

### BE-05-02. Поддержать structured content rendering для ключевых разделов

**Описание:** Сейчас structured rendering есть только для GOAL и ожидает camelCase поля, тогда как часть backend flows использует snake_case. Нужно добавить безопасные renderers для CONTEXT, PROBLEM, GOAL и требований.

**Приоритет:** P1

**Этап:** MMP

**Зависимости:** BE-04-03, frontend artifact schemas.

**Критерии приемки:**
- DOCX корректно рендерит structured content или fallback на plain content.
- Snake_case и camelCase несовместимости обработаны через mapping.
- Некорректный structured content не приводит к 500.

**DoD:** Unit tests для build_docx с полными/частичными/битым structured content; smoke export file opens successfully.

**Labels:** `backend`, `docx`, `structured-content`, `mmp`

### BE-05-03. Добавить export audit metadata

**Описание:** Экспорт должен фиксировать версии артефактов, дату генерации, completion status и source context version, чтобы DOCX был трассируемым.

**Приоритет:** P2

**Этап:** Целевой контур

**Зависимости:** artifact version history, release/documentation requirements.

**Критерии приемки:**
- В DOCX есть таблица или блок metadata по версиям разделов.
- Backend может вернуть export manifest вместе с файлом или отдельным endpoint-ом.
- Export не раскрывает секреты LLM settings.

**DoD:** Tests проверяют manifest; manual QA открывает DOCX; metadata соответствует сохраненным artifact versions.

**Labels:** `backend`, `docx`, `audit`, `target`

## EPIC-BE-06. LLM settings и provider integration

**Название:** Безопасные и управляемые настройки LLM.

**Описание:** Backend хранит `LLMSettings`, поддерживает `mock`, `openrouter`, `corporate`, masked API key, тест подключения через OpenAI-compatible `/chat/completions`, runtime status и readiness gate. Нужно усилить безопасность, валидацию, audit и provider abstraction.

**Приоритет:** P0

**Этап:** MVP

**Зависимости:** security reviewer, DevOps secrets strategy, frontend settings UI.

**Labels:** `backend`, `llm`, `settings`, `security`, `mvp`

### BE-06-01. Ужесточить validation и masking LLM settings

**Описание:** `PUT /settings/llm` принимает `dict`, сохраняет новый row и наследует старый key при masked input. Нужно ввести Pydantic schema, нормализацию provider/base_url/model, bounds для timeout/temperature и единое masking policy.

**Приоритет:** P0

**Этап:** MVP

**Зависимости:** frontend settings form, security review.

**Критерии приемки:**
- API key никогда не возвращается в открытом виде.
- Masked key не затирает сохраненный key.
- Timeout и temperature ограничены допустимыми диапазонами.
- Provider принимает только поддержанные значения.

**DoD:** Tests покрывают create/update/masked key/empty key/invalid provider; OpenAPI содержит schema.

**Labels:** `backend`, `llm`, `validation`, `security`, `mvp`

### BE-06-02. Разделить проверку подключения и сохранение настроек

**Описание:** `POST /settings/llm/test` может сохранять результат проверки как новый `LLMSettings` row. Нужно явно определить, когда тест только проверяет draft settings, а когда обновляет persisted settings.

**Приоритет:** P1

**Этап:** MMP

**Зависимости:** product UX decision, frontend settings flow.

**Критерии приемки:**
- Есть понятный режим dry-run test без сохранения или документированное сохранение.
- Last connection status обновляется предсказуемо.
- Ошибки unauthorized/model_not_found/timeout/backend_error сохраняют безопасные details.

**DoD:** Tests покрывают draft/saved сценарии; frontend не получает неожиданные изменения настроек.

**Labels:** `backend`, `llm`, `settings`, `mmp`

### BE-06-03. Вынести provider clients на расширяемый adapter contract

**Описание:** `OpenRouterLLMClient` и `CorporateLLMClient` наследуют OpenAI-compatible client. Нужно формализовать adapter interface: generate, test_connection, provider metadata, error mapping.

**Приоритет:** P1

**Этап:** MMP

**Зависимости:** BE-02-03, provider requirements.

**Критерии приемки:**
- Provider adapter возвращает typed result с latency, actual model, status, error_code.
- API слой не делает raw urllib request напрямую для provider test.
- Добавление нового provider не требует изменения discovery API logic.

**DoD:** Unit tests для mock/openrouter/corporate adapter behavior; errors мапятся единообразно.

**Labels:** `backend`, `llm`, `provider-adapter`, `mmp`

### BE-06-04. Подготовить secrets-safe storage strategy

**Описание:** API key сейчас хранится в DB field. Для целевого контура нужна стратегия секретов: env/secret manager/encryption at rest, rotation и audit.

**Приоритет:** P2

**Этап:** Целевой контур

**Зависимости:** security reviewer, DevOps engineer, deployment target.

**Критерии приемки:**
- Решено, где физически хранится secret.
- DB не хранит открытый API key без approved encryption strategy.
- Есть rotation/update flow без раскрытия старого key.

**DoD:** ADR или security design approved; implementation покрыта tests; logs/errors не раскрывают credentials.

**Labels:** `backend`, `llm`, `secrets`, `security`, `target`

## EPIC-BE-07. Backend tests и quality gates

**Название:** Расширить backend test coverage под критические flows.

**Описание:** Сейчас есть tests для content extraction, context ingestion и base agent runtime. Нужно добавить API integration tests, repository/versioning tests, LLM settings tests и DOCX export smoke.

**Приоритет:** P0

**Этап:** MVP

**Зависимости:** pytest setup, test DB strategy, QA acceptance scenarios.

**Labels:** `backend`, `tests`, `quality-gate`, `mvp`

### BE-07-01. Добавить FastAPI API tests через TestClient

**Описание:** Покрыть основные endpoint-ы на in-memory/test DB: project CRUD, artifact CRUD, context upload/analyze, generation readiness, completion, runtime status.

**Приоритет:** P0

**Этап:** MVP

**Зависимости:** dependency override для `get_db`, stable test fixtures.

**Критерии приемки:**
- Tests проверяют success и not-found/validation cases.
- LLM readiness gate проверен для mock и not_configured.
- Upload tests не требуют внешней сети.

**DoD:** `pytest` проходит локально; tests документируют expected API behavior.

**Labels:** `backend`, `tests`, `fastapi`, `mvp`

### BE-07-02. Добавить repository/versioning tests

**Описание:** Проверить `create_project`, `update_project`, `delete_project`, `upsert_artifact`, version increment, cascade delete, future uniqueness behavior.

**Приоритет:** P0

**Этап:** MVP

**Зависимости:** artifact constraint decision.

**Критерии приемки:**
- Version увеличивается только при изменении существующего artifact.
- Delete project удаляет artifacts.
- Duplicate artifact behavior определен и покрыт.

**DoD:** Repository tests изолированы от production DB; failures диагностичны.

**Labels:** `backend`, `tests`, `repository`, `versioning`, `mvp`

### BE-07-03. Добавить DOCX export smoke tests

**Описание:** Проверить, что DOCX endpoint и `build_docx` создают валидный `.docx` для пустых, частично заполненных и structured artifacts.

**Приоритет:** P1

**Этап:** MMP

**Зависимости:** DOCX template contract.

**Критерии приемки:**
- Сгенерированный DOCX открывается через `python-docx`.
- Разделы присутствуют в ожидаемом порядке.
- Некорректный structured content не ломает export.

**DoD:** Tests покрывают service и endpoint; binary response headers проверены.

**Labels:** `backend`, `tests`, `docx`, `mmp`

### BE-07-04. Добавить LLM settings и provider error tests

**Описание:** Проверить masking, сохранение настроек, test connection statuses и provider error mapping без реальных внешних запросов.

**Приоритет:** P1

**Этап:** MMP

**Зависимости:** provider adapter contract.

**Критерии приемки:**
- Tests не требуют network.
- Проверены unauthorized, timeout, model_not_found, backend_error.
- API key не появляется в response body.

**DoD:** Mocked adapter/urllib tests стабильны; security-sensitive assertions добавлены.

**Labels:** `backend`, `tests`, `llm`, `security`, `mmp`

## Сквозные open questions

- Нужна ли аутентификация/авторизация для project/artifact/settings endpoint-ов в MVP или это отдельный security epic?
- Что является canonical source of truth для artifact: `content`, `structured_content`, `rich_content_json` или `rendered_html`?
- Должен ли `/settings/llm/test` сохранять настройки при тесте или только валидировать draft payload?
- Нужна ли отдельная таблица для context sources/chunks или JSON внутри CONTEXT artifact достаточно для MVP?
- Какие artifact types входят в обязательный MVP workflow, а какие остаются MMP/target?

## Handoff

Следующие профильные роли:
- `ai-system-analyst`: утвердить API contracts, artifact schemas и stage taxonomy.
- `ai-database-engineer`: спроектировать constraints, migrations, artifact version history и возможные таблицы context sources/chunks.
- `ai-security-reviewer`: проверить LLM settings, secrets handling, upload validation, error/log leakage.
- `ai-qa-engineer` / `ai-test-automation-engineer`: превратить критерии приемки в regression/API test suite.
- `ai-technical-writer`: синхронизировать backlog с общей документацией и DOCX template requirements.

Quality gate для backend: backlog считается готовым к delivery planning после подтверждения API contracts, storage/versioning решения и LLM secrets strategy.
