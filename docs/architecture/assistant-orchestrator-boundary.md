# Граница AI Discovery Chat Orchestrator

Дата: 2026-07-08  
Статус: accepted

## Назначение

AI Discovery Chat - это управляющий application service внутри FastAPI backend. Он принимает пользовательское сообщение, определяет intent, собирает минимальный контекст, проверяет `ToolPolicy`, вызывает stage processors и возвращает assistant response/action для UI.

AI Discovery Chat не является Product AI Agent и не должен жить в `backend/app/agents/`.

## Физические слои

| Слой | Путь | Ответственность |
|---|---|---|
| Assistant orchestration | `discovery-ai-agent/backend/app/assistant/` | Chat intent routing, context assembly, policy gate, assistant action/response сборка. |
| Stage processors | `discovery-ai-agent/backend/app/processors/` | Доменные черновики по этапам через `StageProcessorRequest/StageProcessorResult`. |
| Product AI Agents | `discovery-ai-agent/backend/app/agents/` | Старые и совместимые доменные агенты, `BaseAgent`, `AgentOrchestrator`, agent runtime. |
| Retrieval | `discovery-ai-agent/backend/app/rag/` | `SimpleRetriever`, retrieval query/result, evidence chunks. |
| Corporate sources | `discovery-ai-agent/backend/app/corporate_sources/` | Read-only Corporate Tool Gateway / CorporateSource boundary для будущих MCP/MSP adapters. |
| ApplyPatch security | `discovery-ai-agent/backend/app/services/apply_patch_service.py` | Единственная точка записи proposed patch в `discovery_artifacts` после preview и подтверждения. |

## Разрешённые зависимости

```text
api/discovery.py
  -> assistant/
assistant/
  -> processors/
  -> repositories/
  -> rag/
  -> agents/runtime/
processors/
  -> agents/runtime/
  -> models/
corporate_sources/
  -> agents/runtime/ToolPolicy
agents/
  -> agents/runtime/
```

`assistant/` может импортировать processors, repositories, retrieval и runtime contracts. `processors/` не импортируют frontend, API routes, repositories или Corporate Tool Gateway.

## Запрещённые зависимости

- `agents/ -> assistant/`: Product AI Agents не знают о chat UI и orchestration layer.
- `processors/ -> corporate_sources/`: processors получают только подготовленный retrieval/context contract.
- `processors/ -> repositories/`: processors не пишут и не читают БД напрямую.
- `assistant/ -> frontend/`: backend orchestration не зависит от React implementation.
- `Corporate Tool Gateway -> discovery_artifacts.write`: corporate adapters read-only в MVP.

## Правило proposed patch

AI Discovery Chat не применяет изменения автоматически:

```text
assistant chat message
  -> StageProcessorResult.proposed_patch
  -> assistant action status=proposed
  -> preview в UI
  -> пользователь подтверждает apply
  -> ApplyPatchService проверяет action/project/artifact/status/version/allowlist
  -> discovery_artifacts
```

Если processor для artifact type не подключён, Chat Orchestrator возвращает русское сообщение без `proposed_patch`.

## Q&A по источникам

Обычные вопросы пользователя по загруженным материалам не являются patch-flow. Если `IntentRouter` определяет `answer_from_context` или `search_context_sources`, `DiscoveryChatOrchestrator`:

- использует только `SimpleRetriever` по `CONTEXT` artifact;
- читает `uploaded_files`, `documents`, `links`, `chunks` и `extracted_text`;
- исключает `metadata_only` источники из evidence;
- возвращает `human_message`, `evidence`, `source_trace` и `warnings`;
- не вызывает `StageDraftProcessor`, `RequirementsProcessor` или `ApplyPatchService`;
- не создаёт `proposed_patch`, `assistant action` или preview изменения.

Если `indexing_status = requires_update`, но extracted chunks уже есть, ответ строится по этим chunks и содержит warning: контекст требует обновления, но использован уже извлечённый текст файла.

## Совместимость

Старые Product AI Agents остаются в `backend/app/agents/` для существующих endpoints и fallback-сценариев. Их можно помечать как compatibility/deprecated на уровне docs, но нельзя удалять без отдельного migration plan и regression tests.

`SimpleRetriever` остаётся в `backend/app/rag/simple_retriever.py`. Переименование в `app/retrieval/` возможно только отдельной совместимой миграцией с обновлением импортов и тестов.

`Corporate Tool Gateway` сейчас живёт в `backend/app/corporate_sources/`. Secrets и credentials не должны попадать в repository.
