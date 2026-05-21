# Текущий API contract AI Discovery Platform

Дата фиксации: 2026-05-21  
Статус: factual current contract, без изменения production-кода  
Backlog task: `BE-01-01`

## 1. Назначение документа

Документ фиксирует фактический API contract текущего MVP AI Discovery Platform на основе FastAPI backend, Pydantic schemas, моделей, repository layer, services и текущих frontend consumers.

Это не целевая реализация и не предложение переписать API. Документ нужен как исходная точка для QA, frontend, backend и следующих backlog-задач по унификации ошибок, декомпозиции routers и усилению validation.

## 2. Scope

- Backend FastAPI: `discovery-ai-agent/backend/app/main.py`, `app/api/discovery.py`, schemas, models, repositories, services, product runtime agents и LLM boundary.
- Frontend consumers: `discovery-ai-agent/frontend/src/api/client.ts`, pages и components, которые вызывают backend.
- Текущий контракт фиксируется без изменения кода.
- Документ описывает только Product API текущего приложения. Global Codex Delivery Agents используются как роли разработки и не являются backend services.
- Документ является входом для QA, frontend, backend и backlog-задач `BE-01-02`, `BE-01-03`, `BE-01-04`, `BE-02-01`, `BE-03-01`.

## 3. Общие правила API

Base URL для frontend:

- `VITE_API_URL`, если задан.
- По умолчанию: `http://localhost:8000/api`.
- Health endpoint вызывается отдельно как `http://localhost:8000/health`.

Общие правила:

- Основные API responses возвращаются как JSON.
- DOCX export возвращает binary response с media type `application/vnd.openxmlformats-officedocument.wordprocessingml.document`.
- CORS разрешен для `http://localhost:5173`, `allow_credentials=true`, все методы и headers разрешены.
- Runtime status доступен через `GET /api/runtime/status`.
- LLM readiness проверяется перед генерацией, анализом контекста, validation и AI-вопросами через `_ensure_llm_ready`.
- Ошибки сейчас неоднородны: часть endpoint-ов возвращает `HTTPException(detail="строка")`, часть `HTTPException(detail={ok,error,human_message,details})`, часть endpoint-ов возвращает успешный JSON с `ok`, `last_connection_status`, `last_error`.
- Auth/authz в текущем API отсутствуют.

## 4. Таблица endpoint-ов

| ID | Method | Path | Назначение | Request params | Request body | Success response | Error response | Frontend usage | Текущие проблемы/gaps | Related backlog task |
|---|---|---|---|---|---|---|---|---|---|---|
| API-001 | GET | `/health` | Проверка доступности backend. | Нет. | Нет. | `{ "status": "ok" }` | Не задан кастомный error contract. | `App.tsx` проверяет `http://localhost:8000/health`. | Endpoint вне `/api`; frontend hardcode URL. | BE-01-01 |
| API-002 | GET | `/api/runtime/status` | Статус backend и LLM readiness. | Нет. | Нет. | `{ backend:{status:"ok"}, llm:{provider, configured, ready_for_generation, last_connection_status, model, last_actual_model, last_error, human_message} }` | Не задан кастомный error contract. | `ProjectPage.tsx` через `ensureRuntimeReady`. | Нет Pydantic response schema; `last_error` может содержать provider text. | BE-01-02, BE-06-01 |
| API-003 | GET | `/api/projects` | Получить список проектов. | Нет. | Нет. | `list[ProjectRead]`. | Общие FastAPI errors. | `HomePage.tsx`, `ProjectsPage.tsx`. | Нет pagination/filtering; auth отсутствует. | BE-01-03 |
| API-004 | POST | `/api/projects` | Создать проект. | Нет. | `ProjectCreate`: `project_name` required, `business_domain?`, `jira_epic_url?`. | `ProjectRead`. | Pydantic validation 422; DB errors не унифицированы. | `ProjectsPage.tsx`, clone action. | Минимальная validation; clone передает только `project_name`. | BE-01-04 |
| API-005 | GET | `/api/projects/{project_id}` | Получить проект. | `project_id: str`. | Нет. | `ProjectRead`. | `404 detail="Project not found"`. | `ProjectPage.tsx`. | Английская строка ошибки; нет error envelope. | BE-01-02 |
| API-006 | PATCH | `/api/projects/{project_id}` | Обновить проект. | `project_id: str`. | `ProjectUpdate`: optional `project_name`, `business_domain`, `jira_epic_url`, `status`, `current_stage`. | `ProjectRead`. | `404 detail="Project not found"`, 422 validation. | `ProjectsPage.tsx` архивирует через `{status:"DRAFT"}`. | Нет business validation переходов status/stage. | BE-01-04 |
| API-007 | DELETE | `/api/projects/{project_id}` | Удалить проект. | `project_id: str`. | Нет. | `{ "ok": true }`. | `404 detail="Project not found"`. | `ProjectsPage.tsx`. | Нет audit/soft delete/authz. | BE-01-02, BE-04-02 |
| API-008 | GET | `/api/projects/{project_id}/artifacts` | Получить все artifacts проекта. | `project_id: str`. | Нет. | `list[ArtifactRead]`. | Общие FastAPI/DB errors; проект явно не проверяется. | `ProjectPage.tsx` completion/pipeline load. | Для несуществующего project вернет пустой список; нет project existence check. | BE-01-02 |
| API-009 | GET | `/api/projects/{project_id}/artifacts/{artifact_type}` | Получить artifact по типу. | `project_id: str`, `artifact_type: ArtifactType`. | Нет. | `ArtifactRead`. | `404 detail="Artifact not found"`, 422 invalid enum. | `ProjectPage.tsx` loadArtifact, context/progression flows. | Ошибка на английском; нет проверки существования project отдельно. | BE-01-02, BE-01-04 |
| API-010 | PUT | `/api/projects/{project_id}/artifacts/{artifact_type}` | Создать или обновить artifact. | `project_id: str`, `artifact_type: ArtifactType`. | `ArtifactWrite`: `content`, `structured_content?`, `rich_content_json?`, `rendered_html?`. | `ArtifactRead`; version увеличивается при каждом update. | `404 detail="Project not found"`, 422 validation. | `ProjectPage.tsx` save, context save, problem save, mark dependents stale. | `structured_content` не валидируется по artifact type; нет uniqueness constraint на DB level. | BE-01-04, BE-04-01, BE-04-03 |
| API-011 | POST | `/api/projects/{project_id}/context/sources/upload` | Загрузить context files и извлечь текст/chunks. | `project_id: str`. | `multipart/form-data`, field `files: list[UploadFile]`. | `{ ok:true, sources:[{id, projectId, title, type, fileName, name, size, createdAt, updatedAt, mimeType, status, errorMessage, chunksCount, text_extraction_status, text_extraction_error, text_extracted_at, extracted_text, chunks}] }`. | `404 detail="Проект не найден"`; file-level errors возвращаются внутри `sources`, не как HTTP error. | `ProjectPage.tsx` upload context files через `apiForm`. | API позволяет `xls`, service помечает `xls` unsupported; нет dedup/idempotency; sync extraction в request lifecycle. | BE-03-01, BE-03-02, BE-03-03 |
| API-012 | POST | `/api/projects/{project_id}/context/analyze` | Проанализировать context через `ContextIngestionAgent.analyze`. | `project_id: str`. | Неструктурированный `dict`: `context_input?`, `documents?`, `links?`. | `{ ok:true, extracted_knowledge, source_trace, coverage, readiness, problem_handoff, history_count, indexing_status:"completed" }`. | `400 detail={ok:false,error:"LLM_NOT_READY",human_message,details}`; `404 detail="Проект не найден"`; `500 detail="ContextIngestionAgent не подключен..."`; `400 detail="<ValueError>"`; `400 detail="LLM вернул некорректный JSON"`. | `ProjectPage.tsx` runContextAnalyze. | Request body без Pydantic schema; смешанные error shapes; зависит от runtime agent product layer. | BE-01-02, BE-01-04, BE-03-03 |
| API-013 | POST | `/api/projects/{project_id}/generate/{artifact_type}` | Generic generation artifact через product `AgentOrchestrator`. | `project_id: str`, `artifact_type: ArtifactType`. | Нет. | `ArtifactRead`. | `400 LLM_NOT_READY` dict; `404 detail="Проект не найден"`; `400 detail="Генерация для этого типа артефакта не поддерживается"`; `400 detail="OpenRouter недоступен..."`; raw exceptions могут уйти как 500. | `ProjectPage.tsx` generic generate для stages. | Response shape отличается от stage-specific generators; не все `ArtifactType` поддержаны orchestrator registry. | BE-02-01, BE-02-02, BE-02-04 |
| API-014 | POST | `/api/projects/{project_id}/validate` | Запустить `CriticAgent` и сохранить `VALIDATION_REPORT`. | `project_id: str`. | Нет. | `ArtifactRead`. | `400 LLM_NOT_READY` dict; `404 detail="Проект не найден"`; возможны raw LLM errors. | `ProjectPage.tsx` validate action. | Нет structured validation report schema; ошибки не унифицированы. | BE-01-02, BE-02-01 |
| API-015 | POST | `/api/projects/{project_id}/problem/generate` | Stage-specific генерация PROBLEM. | `project_id: str`. | Optional `dict`, фактически payload не используется как Pydantic schema. | `{ ok:true, structured_content, version }`. | `400 LLM_NOT_READY` dict; `404 detail="Проект не найден"`; `400 detail="Сначала заполните Контекст..."`; LLM JSON fallback может вернуть success с deterministic data. | `ProjectPage.tsx` problem generate. | Response shape отличается от `ArtifactRead`; request body не описан; контекст readiness используется нестрого. | BE-02-01, BE-02-02 |
| API-016 | POST | `/api/projects/{project_id}/problem/ask` | Сформировать локальный patch/assistant message для PROBLEM. | `project_id: str`. | `dict`: `message`, `draft?`. | `{ ok:true, patch:{clarifying_questions, missing_information}, assistant_message }`. | Кастомных ошибок нет; пустой message не валидируется. | `ProjectPage.tsx` askProblem. | Mock-like behavior без LLM readiness; request body без schema. | BE-01-04, BE-02-02 |
| API-017 | POST | `/api/projects/{project_id}/problem/apply-patch` | Применить patch к PROBLEM artifact. | `project_id: str`. | `dict`: `patch`, `status?`. | `{ ok:true, structured_content, version }`. | `404 detail="Артефакт проблемы не найден"`. | `ProjectPage.tsx` applyPatch. | Patch полностью merge без schema/allowlist; response не `ArtifactRead`. | BE-01-04, BE-04-03 |
| API-018 | POST | `/api/projects/{project_id}/goal/generate` | Stage-specific генерация GOAL. | `project_id: str`. | Нет. | `{ ok:true, warning, structured_content, draft, version }`. | `400 LLM_NOT_READY` dict; `404 detail="Проект не найден"`; `400 detail="Сначала заполните Контекст"`; `400 detail={ok:false,error,details,stage,provider,model}` при LLM errors. | `ProjectPage.tsx` goal generate. | Response shape отличается от generic; `_llm_error` не содержит `human_message`; raw details могут содержать provider text. | BE-02-01, BE-02-02, BE-06-01 |
| API-019 | POST | `/api/projects/{project_id}/stage/{artifact_type}/questions` | Сгенерировать уточняющие вопросы для stage. | `project_id: str`, `artifact_type: ArtifactType`. | Нет. | `{ ok:true, questions, structured_content }`. | `400 LLM_NOT_READY` dict; `400 detail="Сначала заполните Контекст"`; raw LLM errors. | `ProjectPage.tsx` loadStageQuestions. | Создает/обновляет artifact даже для unsupported semantic stages; нет response schema. | BE-01-04, BE-02-02 |
| API-020 | POST | `/api/projects/{project_id}/stage/{artifact_type}/ask` | Учесть ответ пользователя и получить AI patch для stage. | `project_id: str`, `artifact_type: ArtifactType`. | `dict`: `message`, `question_id?`. | `{ ok:true, patch, structured_content }`. | `400 LLM_NOT_READY` dict; `400 detail="Введите ответ для AI"`; raw LLM errors. | `ProjectPage.tsx` askStageQuestion/answerQuestion. | Нет Pydantic schema; artifact может отсутствовать и тогда content берется как пустой, но `upsert` создаст artifact. | BE-01-04, BE-02-02 |
| API-021 | POST | `/api/projects/{project_id}/stage/{artifact_type}/apply-patch` | Применить AI patch к stage artifact. | `project_id: str`, `artifact_type: ArtifactType`. | `dict`: `patch?`; если нет, берется `sc.ai_patch`. | `{ ok:true, structured_content }`. | `404 detail="Артефакт не найден"`. | `ProjectPage.tsx` applyStagePatch. | Patch merge без schema/allowlist; не возвращает version. | BE-01-04, BE-04-03 |
| API-022 | GET | `/api/projects/{project_id}/completion` | Рассчитать completion по обязательным sections. | `project_id: str`. | Нет. | `CompletionResponse`: `completion_percent`, `sections`, `required_sections_total`, `required_sections_completed`, `missing_sections`. | `404 detail="Project not found"`. | `HomePage.tsx`, `ProjectPage.tsx`. | Completion зависит от длины `content`, игнорирует часть structured-only stages. | BE-04-03 |
| API-023 | GET | `/api/projects/{project_id}/export/docx` | Скачать DOCX. | `project_id: str`. | Нет. | Binary DOCX stream; header `Content-Disposition: attachment; filename=BT_{project_id}.docx`. | `404 detail="Project not found"`; service exceptions как 500. | `ProjectPage.tsx`, `ProjectsPage.tsx` через `window.open`/link. | Нет export manifest, audit metadata, structured rendering ограничен GOAL. | BE-05-01, BE-05-02, BE-05-03 |
| API-024 | GET | `/api/settings/llm` | Получить masked LLM settings и connection status. | Нет. | Нет. | `{ ok:true, provider, base_url, model, api_key(masked), key_tail, timeout_seconds, temperature, last_connection_status, last_latency_ms, last_actual_model, last_error, human_message }`. | Общие DB errors. | `App.tsx`, `LLMSettingsPage.tsx`. | Нет Pydantic response schema; `last_error` возвращается наружу. | BE-06-01 |
| API-025 | PUT | `/api/settings/llm` | Сохранить LLM settings. | Нет. | Неструктурированный `dict`: `provider`, `base_url`, `api_key`, `model`, `timeout_seconds`, `temperature`. | Такой же shape, как `GET /settings/llm`. | Общие DB/type errors; нет validation bounds. | `LLMSettingsPage.tsx` save. | Request body без schema; masked key inheritance не документирован в OpenAPI. | BE-01-04, BE-06-01 |
| API-026 | POST | `/api/settings/llm/test` | Проверить LLM connection и сохранить результат как новый `LLMSettings` row. | Нет. | Optional `dict`: draft settings; `max_tokens?`. | Такой же shape, как `GET /settings/llm`; `last_connection_status` один из LLM statuses. | HTTP provider errors не бросаются наружу, а сохраняются в response status; backend exception также мапится в `timeout`/`backend_error` row. | `LLMSettingsPage.tsx` test. | Test mutates persisted settings; raw provider error fragment может попасть в `last_error`. | BE-06-02, BE-06-03 |

## 5. Enum-значения

### ArtifactType

- `CONTEXT`
- `PROBLEM`
- `GOAL`
- `BUSINESS_EFFECT`
- `AS_IS`
- `TO_BE`
- `USE_CASES`
- `FUNCTIONAL_REQUIREMENTS`
- `NON_FUNCTIONAL_REQUIREMENTS`
- `RISKS`
- `GLOSSARY`
- `FINAL_BT`
- `VALIDATION_REPORT`

### ProjectStatus

- `DRAFT`
- `IN_PROGRESS`
- `BT_READY`
- `APPROVED`

### ProjectStage

- `CONTEXT`
- `PROBLEM`
- `GOAL`
- `BUSINESS_EFFECT`
- `AS_IS`
- `TO_BE`
- `USE_CASES`
- `REQUIREMENTS`
- `RISKS`
- `FINAL_BT`
- `VALIDATION_REPORT`

Важно: `ProjectStage.REQUIREMENTS` не совпадает по имени с `ArtifactType.FUNCTIONAL_REQUIREMENTS`.

### LLM status

Набор backend statuses:

- `mock`
- `not_configured`
- `connected`
- `error`
- `timeout`
- `unauthorized`
- `model_not_found`
- `backend_error`

Runtime readiness:

- `configured: boolean`
- `ready_for_generation: boolean`

### Completion section statuses

- `not_started`
- `in_progress`
- `completed`

### Context source statuses

Frontend/source status:

- `uploaded`
- `ready`
- `empty`
- `unsupported`
- `error`
- `indexing` используется frontend во время анализа.

Text extraction status:

- `completed`
- `empty`
- `unsupported`
- `failed`

Indexing status в `CONTEXT.structured_content`:

- `idle` используется frontend при первичном создании context artifact.
- `requires_update` ставится после upload.
- `completed` ставится после analyze.

## 6. Текущий error contract

Фактическая ситуация неоднородна.

Строковый `detail`:

- `Project not found`
- `Artifact not found`
- `Проект не найден`
- `Артефакт проблемы не найден`
- `Артефакт не найден`
- `Сначала заполните Контекст`
- `Сначала заполните Контекст или загрузите источники знаний.`
- `Введите ответ для AI`
- `LLM вернул некорректный JSON`
- `OpenRouter недоступен. Проверьте API key, модель и интернет-соединение.`
- `Генерация для этого типа артефакта не поддерживается`
- `ContextIngestionAgent не подключен в AgentOrchestrator`

Dict payload в `detail`:

- `_ensure_llm_ready` возвращает `400` с `{ok:false,error:"LLM_NOT_READY",human_message,details}`.
- `_llm_error` для GOAL возвращает `{ok:false,error,details,stage,provider,model}` без `human_message`.

Success payload с `ok/error/details`:

- Upload возвращает `ok:true`, а file-level extraction errors лежат внутри `sources[*].errorMessage` и `text_extraction_error`.
- LLM settings test не всегда возвращает HTTP error: provider/test failures сохраняются как `last_connection_status` и `last_error` в success JSON.

Русские human messages:

- `_status_message` возвращает русские сообщения для LLM status.
- `_ensure_llm_ready` возвращает `human_message` на русском.
- Upload и context/stage errors частично на русском.
- CRUD project/artifact errors частично на английском.

Где нужно унифицировать:

- Все `HTTPException` должны возвращать единый error envelope.
- `404`, `400`, provider errors, validation errors, unsupported generation и extraction errors должны иметь стабильный `error_code`.
- `last_error` provider должен быть безопасно обрезан и очищен от secrets/private endpoint fragments.
- Frontend `parseApiError` уже ожидает `human_message`, `detail.human_message`, `detail.error`, `error`, но это fallback logic, а не стабильный contract.

## 7. Целевой error envelope для следующей задачи BE-01-02

Рекомендуемый формат для следующей задачи. В рамках BE-01-01 код не реализуется.

```json
{
  "ok": false,
  "error_code": "ERROR_CODE",
  "human_message": "Сообщение на русском языке",
  "details": {},
  "trace_id": "optional"
}
```

Рекомендации:

- `error_code` должен быть стабильным машинным кодом: `PROJECT_NOT_FOUND`, `ARTIFACT_NOT_FOUND`, `LLM_NOT_READY`, `UNSUPPORTED_ARTIFACT_TYPE`, `VALIDATION_ERROR`, `CONTEXT_EXTRACTION_FAILED`.
- `human_message` всегда на русском языке.
- `details` не содержит API keys, bearer tokens, private headers, полный закрытый provider response.
- `trace_id` опционален до внедрения runtime telemetry.

## 8. Gaps и риски

- Неоднородные ошибки: строковый `detail`, dict payload, success JSON с error-status внутри.
- Dict payload без Pydantic схем: `context/analyze`, `problem/*`, `stage/*`, `settings/llm`, `settings/llm/test`.
- Отсутствует auth/authz для projects, artifacts, settings и export.
- Отсутствует audit для изменения проектов, артефактов, LLM settings, export и delete.
- Startup schema patch добавляет columns на startup вместо полноценной миграции.
- Generic `/generate/{artifact_type}` и stage-specific `/problem/generate`, `/goal/generate`, `/stage/*` имеют разный response shape.
- `ProjectStage.REQUIREMENTS` и `ArtifactType.FUNCTIONAL_REQUIREMENTS` расходятся по taxonomy.
- Upload поддерживает `xls` на API allowlist уровне, но extraction service возвращает `unsupported`.
- Completion опирается на plain `content`, что может не отражать structured-only artifacts.
- `GET /projects/{project_id}/artifacts` не проверяет существование project.
- `POST /settings/llm/test` не является pure test: он сохраняет новый settings row.
- Product AI Agents используются только как runtime продукта; Global Codex Delivery Agents не являются API services.

## 9. Связь со следующими backlog-задачами

- `BE-01-02` error envelope: использовать разделы 6-7 как baseline для унификации ошибок.
- `BE-01-03` decomposition routers: таблица endpoint-ов задает зоны для routers: projects, artifacts, context, generation, stage assistance, export, settings/runtime.
- `BE-01-04` Pydantic validation: endpoint-ы с `dict` body перечислены как кандидаты на typed schemas.
- `BE-02-01` AgentResult contract: generic и stage-specific generation response shapes перечислены как текущие расхождения.
- `BE-03-01` context extraction matrix: upload/analyze statuses и `xls` gap зафиксированы.

## 10. Acceptance checklist

- [x] Все endpoint-ы из задачи описаны.
- [x] Request params указаны.
- [x] Request body shapes указаны.
- [x] Success response shapes указаны.
- [x] Error response shapes описаны.
- [x] Frontend usage зафиксирован.
- [x] Enum-значения указаны.
- [x] Текущие gaps вынесены.
- [x] Явно указано, что это current/factual contract, а не целевая реализация.
- [x] Product AI Agents и Global Codex Delivery Agents не смешаны.
- [x] Production-код не изменялся.

