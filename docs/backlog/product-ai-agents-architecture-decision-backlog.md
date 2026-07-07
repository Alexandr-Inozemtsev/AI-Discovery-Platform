# Backlog: архитектурное решение по Product AI Agents

Дата: 2026-05-22  
Статус: draft backlog и manual Trello import/update package
Trello board: https://trello.com/b/AKdFcJsw/aidiscoveryplatform
Важно: карточки ниже относятся к delivery-процессу разработки. Ответственные `ai-*` роли являются Global Codex Delivery Agents, а не runtime-агентами продукта. Trello API/UI не вызывались, доска не синхронизировалась.

## Основание

Экспертный review в [docs/architecture/product-ai-agents-architecture-review.md](../architecture/product-ai-agents-architecture-review.md) рекомендует не расширять текущую модель “один Product AI Agent class на каждый Discovery stage”, а перейти к гибридной целевой модели:

- отдельный `ContextIngestionAgent`;
- `StageDraftProcessor` для Problem/Goal/BusinessEffect/UseCases;
- `RequirementsProcessor` для требований и Final BT;
- отдельный `CriticAgent` / `ValidationProcessor`;
- единый Agent Runtime, Prompt Registry, LLM Gateway и SimpleRetriever.

Phase 1 chat-first update от 2026-07-08 добавляет [ADR-004 AI Discovery Chat Architecture](../architecture/ADR-004-ai-discovery-chat-architecture.md): AI Discovery Chat становится единой точкой входа в workflow, а формы этапов остаются structured state артефактов. Запись в `discovery_artifacts` разрешена только через `proposed_patch -> preview -> apply`.

## Backlog items

### ARCH-CHAT-01. ADR-004 AI Discovery Chat Architecture

Список Trello: `03 Architecture / ADR`  
Labels: `Архитектура`, `Chat UX`, `Agent Runtime`, `MVP`  
Ответственный агент: `ai-product-orchestrator`  
Участники: `ai-solution-architect`, `ai-system-analyst`, `ai-security-reviewer`, `ai-frontend-developer`, `ai-backend-developer`  
Приоритет: P0  
Этап: MVP  
Статус: Done in Phase 1

Цель: зафиксировать chat-first архитектуру, где AI Discovery Chat является единой точкой входа, а текущие формы этапов остаются structured state артефактов.

Acceptance criteria:

- ADR-004 создан и связан с ADR-003.
- FastAPI/React runtime сохраняется.
- Product AI Agents не смешаны с Global Codex Delivery Agents.
- Запрещена прямая запись AI-чата в `discovery_artifacts`.
- Зафиксирована цепочка `proposed_patch -> preview -> apply`.

### ARCH-CHAT-02. Обновить связку ADR-003 и Chat Orchestrator

Список Trello: `03 Architecture / ADR`  
Labels: `Архитектура`, `Chat Orchestrator`, `Agent Runtime`, `MVP`  
Ответственный агент: `ai-solution-architect`  
Участники: `ai-product-orchestrator`, `ai-system-analyst`, `ai-backend-developer`  
Приоритет: P0  
Этап: MVP  
Статус: Done in Phase 1

Цель: показать, что ADR-003 описывает Product AI Agents runtime foundation, а ADR-004 и Chat Orchestrator описывают пользовательскую orchestration-границу.

Acceptance criteria:

- ADR-003 содержит ссылку на ADR-004.
- Создан `Chat Orchestrator Contract`.
- Описаны intent routing, ToolPolicy, StageProcessorRequest/Result и apply gate.

### BE-RUNTIME-01. StageProcessorRequest/StageProcessorResult

Список Trello: `03 Architecture / ADR`  
Labels: `Backend`, `Agent Runtime`, `API Contract`, `MVP`  
Ответственный агент: `ai-backend-developer`  
Участники: `ai-system-analyst`, `ai-qa-engineer`, `ai-llm-rag-engineer`  
Приоритет: P0  
Этап: MVP  
Статус: Done in Phase 1

Цель: ввести минимальный runtime contract для stage processors до реализации Chat Orchestrator и StageDraftProcessor.

Acceptance criteria:

- Добавлены runtime dataclasses `StageProcessorRequest` и `StageProcessorResult`.
- Result содержит `proposed_patch`, `preview`, `human_message`, evidence/open questions/warnings/errors.
- Request имеет проверку secret-like fields.
- Контракт покрыт backend tests.

### SEC-CHAT-01. ToolPolicy для AI Discovery Chat

Список Trello: `03 Architecture / ADR`  
Labels: `Security`, `Chat UX`, `Agent Runtime`, `MVP`  
Ответственный агент: `ai-security-reviewer`  
Участники: `ai-product-orchestrator`, `ai-backend-developer`, `ai-qa-engineer`  
Приоритет: P0  
Этап: MVP  
Статус: Done in Phase 1

Цель: запретить AI Discovery Chat прямую запись в `discovery_artifacts` и доступ к secrets, разрешив только read/proposed_patch/preview/apply с подтверждением.

Acceptance criteria:

- `ToolPolicy.for_ai_discovery_chat()` описывает allowlist/denylist.
- `patch.apply` требует `requires_user_confirmation=True`.
- `discovery_artifacts.write` запрещен.
- Security requirements обновлены.

### ARCH-PA-01. Remediation и approval ADR-003 по целевой модели Product AI Agents

Список Trello: `03 Architecture / ADR`  
Labels: `Архитектура`, `Agent Runtime`, `MVP`, `Риск`  
Ответственный агент: `ai-solution-architect`  
Участники: `ai-product-orchestrator`, `ai-system-analyst`, `ai-security-reviewer`, `ai-qa-engineer`  
Приоритет: P0  
Этап: MVP  
Статус: Remediation Done, approval pending

Цель: устранить конфликт ADR-нумерации и подготовить к утверждению архитектурное решение [ADR-003 Product AI Agents target architecture](../architecture/ADR-003-product-ai-agents-target-architecture.md).

Описание: review показал, что часть Product AI Agents является stage-specific prompt wrappers. До production refactor нужно устранить конфликт нумерации, сохранить `ADR-002` за target platform evolution и принять или отклонить гибридную модель в `ADR-003`.

Dependencies:

- `docs/architecture/product-ai-agents-architecture-review.md`;
- `docs/architecture/product-ai-agents-target-architecture.md`;
- `docs/architecture/ADR-003-product-ai-agents-target-architecture.md`;
- `docs/architecture/agent-runtime-contract.md`;
- `docs/architecture/simple-retriever-contract.md`;
- `docs/llm-rag/rag-and-retrieval-target-design.md`;
- `BE-02-01`;
- `BE-02-02`.

Acceptance criteria:

- Конфликт ADR-нумерации устранён: Product AI Agents ADR имеет номер `ADR-003`.
- ADR прочитан и принят/отклонён владельцем архитектуры.
- Чётко указано, остаётся ли текущая модель или начинается migration.
- Product AI Agents не смешаны с Global Codex Delivery Agents.
- Corporate wording согласован: единый Agent Runtime с режимами генерации, а не отдельные AI-сервисы.

Definition of Done:

- ADR filename и заголовок соответствуют номеру `ADR-003`.
- ADR имеет финальный статус после approval.
- Backlog/Gantt отражают принятое решение.
- Trello manual card готова к переносу.
- Нет изменений production runtime.

### BE-02-05. Спроектировать StageProcessorRequest/StageProcessorResult

Список Trello: `03 Architecture / ADR`  
Labels: `Backend`, `Agent Runtime`, `API Contract`, `MVP`  
Ответственный агент: `ai-system-analyst`  
Участники: `ai-backend-developer`, `ai-llm-rag-engineer`, `ai-qa-engineer`  
Приоритет: P0  
Этап: MVP  
Статус: Draft

Цель: зафиксировать единый contract для stage processors до реализации `StageDraftProcessor`.

Acceptance criteria:

- Описаны поля request/result.
- Описаны evidence, assumptions, open_questions, warnings, errors.
- Описаны backward compatibility rules для существующих endpoint paths.
- Описаны tests и QA gates.

### BE-02-06. Подготовить миграцию stage prompt wrappers в StageDraftProcessor

Список Trello: `04 Ready for Development`  
Labels: `Backend`, `LLM/RAG`, `Refactoring`, `MMP`  
Ответственный агент: `ai-backend-developer`  
Участники: `ai-solution-architect`, `ai-llm-rag-engineer`, `ai-test-automation-engineer`, `ai-security-reviewer`  
Приоритет: P1  
Этап: MMP  
Статус: Draft

Цель: подготовить безопасный план миграции `ProblemAgent`, `GoalAgent`, `BusinessEffectAgent`, `UseCaseAgent` в processor/template model.

Acceptance criteria:

- Existing endpoint paths не меняются.
- Есть compatibility wrappers или migration mapping.
- Добавлены tests на existing behavior.
- Prompt templates имеют versions.
- `source_trace` и retrieval evidence учтены.

### QA-PA-01. Подготовить prompt regression и golden datasets для stage processors

Список Trello: `07 QA / Testing`  
Labels: `QA`, `LLM/RAG`, `Agent Runtime`, `MVP`  
Ответственный агент: `ai-qa-engineer`  
Участники: `ai-test-automation-engineer`, `ai-llm-rag-engineer`  
Приоритет: P0  
Этап: MVP  
Статус: Draft

Цель: сделать будущую migration проверяемой.

Acceptance criteria:

- Есть 10-20 golden cases для Problem.
- Есть 10-20 golden cases для Goal.
- Есть 10-20 golden cases для Requirements.
- Есть checks для empty context, metadata-only sources, missing evidence, fallback, hallucination.

## Manual Trello import package

### Card 1

Title: `ARCH-PA-01 Remediation и approval ADR-003 по Product AI Agents`

Description:

```text
Цель: устранить конфликт ADR-нумерации и принять архитектурное решение по целевой модели Product AI Agents в AI Discovery Platform.

Контекст:
- текущие stage agents частично являются prompt wrappers;
- ContextIngestionAgent является отдельным специализированным компонентом;
- RequirementsAgent уже переиспользуется для нескольких artifact types;
- ADR-002 сохраняется за target platform evolution;
- ADR-003 используется для Product AI Agents target architecture;
- рекомендуемая модель: единый Agent Runtime + ContextIngestionAgent + StageDraftProcessor + RequirementsProcessor + CriticAgent.

Source docs:
- docs/architecture/product-ai-agents-architecture-review.md
- docs/architecture/product-ai-agents-target-architecture.md
- docs/architecture/ADR-003-product-ai-agents-target-architecture.md
- docs/backlog/product-ai-agents-architecture-decision-backlog.md

Responsible agent: ai-solution-architect
Priority: P0
Labels: Архитектура, Agent Runtime, MVP, Риск
Dependencies: BE-02-01, BE-02-02, SimpleRetriever contract, RAG target design

Acceptance criteria:
- Конфликт ADR-нумерации устранён.
- ADR-003 принят или отклонён владельцем архитектуры.
- Зафиксировано, нужна ли migration.
- Product AI Agents не смешаны с Global Codex Delivery Agents.
- Corporate wording согласован.

Definition of Done:
- ADR filename/title/status обновлены.
- Backlog/Gantt отражают решение.
- Production-код не менялся в рамках decision task.
```

Checklist:

- Прочитать architecture review.
- Проверить, что ADR-003 свободен.
- Убедиться, что ADR-002 target platform evolution сохранён.
- Подтвердить или отклонить гибридную модель.
- Согласовать corporate wording.
- Уточнить MVP/MMP migration scope.
- Обновить delivery plan при принятии migration.

### Card 2

Title: `BE-02-05 Спроектировать StageProcessor contract`

Description:

```text
Цель: описать StageProcessorRequest и StageProcessorResult для будущей миграции Product AI Agents.

Responsible agent: ai-system-analyst
Priority: P0
Labels: Backend, Agent Runtime, API Contract, MVP
Dependencies: ARCH-PA-01, BE-02-01

Acceptance criteria:
- Request/result contract описан.
- Evidence/source_trace/assumptions/open_questions описаны.
- Backward compatibility rules для API paths описаны.
- QA strategy указана.
```

Checklist:

- Описать request fields.
- Описать result fields.
- Описать evidence contract.
- Описать validation/fallback policy.
- Подготовить handoff для backend и QA.

## Trello sync status

- Trello board: https://trello.com/b/AKdFcJsw/aidiscoveryplatform
- Trello API/UI не вызывались.
- Этот файл является manual import/update package.
- Нельзя утверждать, что карточки созданы на доске, пока пользователь не перенесёт их вручную или не будет подключен Trello API.
