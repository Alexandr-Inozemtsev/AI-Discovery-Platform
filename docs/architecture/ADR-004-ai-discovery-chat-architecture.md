# ADR-004: Архитектура AI Discovery Chat

Дата: 2026-07-08  
Статус: accepted for Phase 1  
Scope: chat-first UX, Product AI Agents, Chat Orchestrator, stage processor contracts, ToolPolicy  
Не scope: замена FastAPI/React runtime, Global Codex Delivery Agents, прямое изменение `discovery_artifacts` из AI-чата.

## Контекст

AI Discovery Platform уже имеет FastAPI backend, React frontend, Product AI Agents и structured state в `discovery_artifacts`. Текущий UX построен вокруг форм этапов Discovery. Целевое изменение: AI Discovery Chat становится единой точкой входа для управления Discovery workflow, а формы этапов остаются проверяемыми structured state артефактов.

Ключевое ограничение: chat не становится внешней платформой и не получает право напрямую писать в `discovery_artifacts`. Любое изменение артефакта проходит через цепочку:

```text
user message -> Chat Orchestrator -> StageProcessorRequest -> StageProcessorResult
             -> proposed_patch -> preview -> apply -> discovery_artifacts
```

## Решение

Принять chat-first архитектуру поверх существующего FastAPI/React runtime:

- React сохраняется как основной frontend runtime и добавляет AI Discovery Chat как главный пользовательский workflow surface.
- FastAPI сохраняется как backend runtime и предоставляет Chat Orchestrator как internal application service.
- Product AI Agents остаются внутри product runtime и не смешиваются с Global Codex Delivery Agents.
- Текущие формы этапов Discovery остаются structured state editor/viewer для `discovery_artifacts`.
- Chat Orchestrator управляет намерением пользователя, чтением state, выбором stage processor, preview и apply gate.
- Stage processors возвращают `StageProcessorResult`, а не пишут в БД напрямую.
- Apply step выполняет backend application service после явного действия пользователя или подтвержденного UI command.
- Chat-specific application service код находится в `discovery-ai-agent/backend/app/assistant/`.
- Product AI Agents остаются в `discovery-ai-agent/backend/app/agents/`; chat orchestration не должен располагаться в этом пакете и Product AI Agents не импортируют assistant layer.
- Stage processors находятся в `discovery-ai-agent/backend/app/processors/` и являются доменным processing layer для `StageProcessorRequest/StageProcessorResult`.
- Retrieval boundary остается в `discovery-ai-agent/backend/app/rag/simple_retriever.py`; перенос в `app/retrieval/` возможен отдельным ADR, но assistant/processors не должны читать полный корпус документов напрямую.
- Corporate source boundary сейчас расположен в `discovery-ai-agent/backend/app/corporate/`; целевое имя пакета `app/corporate_sources/` допускается только через совместимую миграцию без хранения credentials в repo.
- Chat Orchestrator не строит domain patch самостоятельно: он маршрутизирует intent, собирает context, проверяет `ToolPolicy` и делегирует stage-specific результат processors.
- Corporate Tool Gateway/MCP boundary находится вне processors; processors получают только подготовленный retrieval/context contract.

## Физическая структура backend

```text
backend/app/
  assistant/
    discovery_chat_orchestrator.py
    intent_router.py
    chat_context_assembler.py
    assistant_action_builder.py
    assistant_response_builder.py
    prompt_templates.py
  processors/
    stage_draft_processor.py
    requirements_processor.py
    validation_processor.py
  agents/
    base_agent.py
    orchestrator.py
    context_ingestion_agent.py
    problem_agent.py
    goal_agent.py
    business_effect_agent.py
    use_case_agent.py
    requirements_agent.py
    critic_agent.py
  rag/
    simple_retriever.py
  corporate/
    tool_gateway.py
```

`AI Discovery Chat` является управляющим application service, а не Product AI Agent. Его зависимости направлены вниз: `assistant -> processors/repositories/rag/runtime`. Обратная зависимость `agents -> assistant` запрещена.

## Компоненты

| Компонент | Назначение |
|---|---|
| `AI Discovery Chat UI` | Единая точка входа: вопросы, команды, объяснение состояния, preview патчей. |
| `Chat Orchestrator` | Определяет intent, stage, policy, вызывает processors и собирает user-facing ответ на русском языке. |
| `Assistant Action Builder` | Собирает metadata для assistant actions без доменной генерации patch. |
| `Assistant Response Builder` | Собирает guidance/policy/unsupported responses без записи в артефакты. |
| `ToolPolicy` | Allowlist/denylist действий чата: read, proposed_patch, preview, apply с подтверждением; запрет прямой записи. |
| `StageProcessorRequest` | Typed input boundary для stage processors без secrets и лишних документов. |
| `StageProcessorResult` | Typed output boundary: content, structured content, evidence, assumptions, open questions, proposed_patch, preview. |
| `StageDraftProcessor` | Готовит structured draft для `PROBLEM`, `GOAL`, `BUSINESS_EFFECT`, `USE_CASES`. |
| `RequirementsProcessor` | Готовит structured requirements/final BT patches для `FUNCTIONAL_REQUIREMENTS`, `NON_FUNCTIONAL_REQUIREMENTS`, `FINAL_BT`. |
| `ValidationProcessor` | Готовит validation report без автоматического patch к бизнес-артефактам. |
| `Corporate Tool Gateway` | Read-only boundary для CorporateSource/MCP/MSP adapters; не хранит secrets в repo и не находится внутри stage processors. |
| `Patch Preview Service` | Показывает diff/изменяемые поля до записи. |
| `Apply Patch Service` | Единственная точка записи patch в `discovery_artifacts` после подтверждения. |

## Контракт данных

`StageProcessorRequest` содержит только необходимые данные:

- `project_id`, `artifact_type`, `stage_type`;
- `project_snapshot`;
- версии и содержимое нужных upstream artifacts;
- `context_readiness`;
- `retrieval_result` с chunks/evidence;
- `user_answers`;
- `prompt_version`, `trace_id`, `metadata`.

Запрещено включать API keys, bearer tokens, cookies, private provider headers, MCP credentials и полные документы, если достаточно chunks.

`StageProcessorResult` возвращает:

- `ok`, `artifact_type`, `content`, `structured_content`;
- `proposed_patch` и `preview` для human-in-the-loop изменения;
- `human_message` на русском языке;
- `evidence`, `source_trace`, `assumptions`, `open_questions`;
- `warnings`, `errors`, `used_fallback`, `metadata`.

## Security decision

Для AI Discovery Chat вводится `ToolPolicy`:

- разрешено: читать проект/артефакты/status, создавать proposed patch, preview patch, задавать уточняющие вопросы;
- разрешено условно: `patch.apply` только после user confirmation;
- запрещено: `discovery_artifacts.write`, чтение credentials, запись LLM secrets, raw prompt logging без redaction policy;
- недоверенный context из файлов/ссылок не может задавать tool instructions.
- `ApplyPatchService` дополнительно проверяет `artifact_type`, allowlist полей для каждого artifact type, статус action и optimistic version conflict.
- Unknown fields в `proposed_patch` отклоняются до записи в `discovery_artifacts`.

## Совместимость

Существующие endpoints сохраняются:

- `/api/projects/{project_id}/generate/{artifact_type}`;
- `/api/projects/{project_id}/problem/generate`;
- `/api/projects/{project_id}/goal/generate`;
- `/api/projects/{project_id}/stage/{artifact_type}/questions`;
- `/api/projects/{project_id}/stage/{artifact_type}/ask`;
- `/api/projects/{project_id}/stage/{artifact_type}/apply-patch`;
- `/api/projects/{project_id}/validate`.

Chat-first UX добавляется поверх них и будущих chat endpoints. Текущие формы этапов не удаляются и остаются fallback/manual editing surface.

## Последствия

Положительные:

- один пользовательский вход в Discovery workflow;
- структурированные артефакты сохраняют проверяемость и экспортируемость;
- безопасный human-in-the-loop gate для AI-изменений;
- меньше разрыва между chat-сценариями и forms state;
- Product AI Agents остаются внутри собственного backend runtime.

Отрицательные:

- нужен новый слой intent routing и patch preview;
- нужно унифицировать patch schema по artifact types;
- требуется QA на запрет прямой записи и prompt injection сценарии;
- frontend должен уметь показывать preview/diff и apply states.

## Phase 2 handoff

Готовы к разработке:

- backend Chat Orchestrator service за существующим FastAPI runtime;
- chat endpoint contract без изменения существующих paths;
- patch preview/apply service с allowlist полей по artifact type;
- frontend AI Discovery Chat shell как главный project workspace surface;
- regression tests на `proposed_patch -> preview -> apply`.

## Rollback

Rollback не требует миграции данных:

- отключить chat-first route/feature flag;
- оставить stage forms и текущие endpoints;
- не применять proposed patches без apply;
- сохранить `StageProcessorRequest/Result` как internal contract для будущей миграции.

## Связанные документы

- [ADR-003 Product AI Agents target architecture](ADR-003-product-ai-agents-target-architecture.md);
- [Chat Orchestrator contract](chat-orchestrator-contract.md);
- [Agent Runtime Contract](agent-runtime-contract.md);
- [Assistant Orchestrator Boundary](assistant-orchestrator-boundary.md);
- [Product AI Agents target architecture](product-ai-agents-target-architecture.md);
- [Security requirements](../security/security-requirements.md);
- [Product AI Agents architecture decision backlog](../backlog/product-ai-agents-architecture-decision-backlog.md).
