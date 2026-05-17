# Целевая модель данных AI Discovery Platform

Дата: 2026-05-17

## Текущее состояние

В backend уже есть основные сущности:
- `DiscoveryProject`: проект, домен, статус, текущий этап, ссылка на Jira epic, timestamps.
- `DiscoveryArtifact`: артефакт проекта, тип, `content`, `structured_content`, `rich_content_json`, `rendered_html`, версия, timestamps.
- `LLMSettings`: настройки provider, base URL, model, masked key state, connection status.

Контекстные источники и chunks сейчас в основном живут внутри `DiscoveryArtifact.structured_content` для `CONTEXT`.

## Целевые сущности

### `DiscoveryProject`

Назначение: корневая сущность Discovery.
Дополнить:
- `owner_user_id`
- `workspace_id`
- `archived_at`
- `readiness_status`
- `last_exported_at`

### `ContextSource`

Назначение: отдельный источник контекста.
Поля:
- `id`
- `project_id`
- `source_type`: file, url, manual
- `title`
- `uri`
- `file_name`
- `mime_type`
- `size_bytes`
- `status`
- `version`
- `checksum`
- `extracted_text_ref`
- `error_message`
- `created_at`
- `updated_at`

### `SourceChunk`

Назначение: фрагмент текста для retrieval.
Поля:
- `id`
- `source_id`
- `project_id`
- `chunk_index`
- `text`
- `metadata`
- `start_offset`
- `end_offset`
- `content_hash`
- `created_at`

### `ArtifactVersion`

Назначение: история версий артефактов.
Поля:
- `id`
- `artifact_id`
- `project_id`
- `artifact_type`
- `version`
- `content`
- `structured_content`
- `source_artifact_versions`
- `source_trace`
- `created_by`
- `created_at`

### `AgentRun`

Назначение: журнал запуска AI-агента.
Поля:
- `id`
- `trace_id`
- `project_id`
- `artifact_type`
- `agent_name`
- `prompt_version`
- `llm_provider`
- `llm_model`
- `actual_model`
- `input_artifact_versions`
- `retrieval_hits`
- `status`
- `warnings`
- `errors`
- `used_fallback`
- `latency_ms`
- `created_at`

### `AuditEvent`

Назначение: аудит пользовательских и системных действий.
Поля:
- `id`
- `project_id`
- `actor_id`
- `actor_type`
- `event_type`
- `entity_type`
- `entity_id`
- `before_hash`
- `after_hash`
- `metadata`
- `created_at`

### `PromptVersion`

Назначение: контроль версий prompt-ов.
Поля:
- `id`
- `agent_name`
- `prompt_key`
- `version`
- `template_hash`
- `description`
- `status`
- `created_at`

## Версионирование

- Каждое сохранение артефакта создаёт snapshot в `ArtifactVersion`.
- Изменение источника переводит зависимые артефакты в состояние `stale`.
- `source_artifact_versions` фиксирует, на каких версиях построен результат.
- Rollback возвращает конкретную версию артефакта и создаёт новое audit event.

## Хранение chunks

- Chunks должны храниться отдельно от `structured_content`.
- Каждый chunk связан с версией источника.
- Chunk text должен иметь hash для проверки повторной индексации.
- На первом этапе не требуется vector store.

## Audit log

Обязательные события:
- создание проекта;
- изменение статуса проекта;
- загрузка источника;
- извлечение текста;
- запуск агента;
- сохранение артефакта;
- экспорт DOCX;
- изменение LLM settings;
- ошибка LLM или extraction.

## Migration backlog

1. Создать таблицы `context_sources` и `source_chunks`.
2. Мигрировать текущие documents/links из `CONTEXT.structured_content`.
3. Создать `artifact_versions`.
4. Создать `agent_runs`.
5. Создать `audit_events`.
6. Добавить индексы по `project_id`, `artifact_type`, `source_id`, `trace_id`, `created_at`.
7. Добавить обратную совместимость чтения старого `structured_content`.
