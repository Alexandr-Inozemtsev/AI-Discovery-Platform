# Backlog: архитектурное решение по Product AI Agents

Дата: 2026-05-22  
Статус: draft backlog и manual Trello import package  
Важно: карточки ниже относятся к delivery-процессу разработки. Ответственные `ai-*` роли являются Global Codex Delivery Agents, а не runtime-агентами продукта. Trello API не вызывался, доска не синхронизировалась.

## Основание

Экспертный review в [docs/architecture/product-ai-agents-architecture-review.md](../architecture/product-ai-agents-architecture-review.md) рекомендует не расширять текущую модель “один Product AI Agent class на каждый Discovery stage”, а перейти к гибридной целевой модели:

- отдельный `ContextIngestionAgent`;
- `StageDraftProcessor` для Problem/Goal/BusinessEffect/UseCases;
- `RequirementsProcessor` для требований и Final BT;
- отдельный `CriticAgent` / `ValidationProcessor`;
- единый Agent Runtime, Prompt Registry, LLM Gateway и SimpleRetriever.

## Backlog items

### ARCH-PA-01. Утвердить ADR по целевой модели Product AI Agents

Список Trello: `03 Architecture / ADR`  
Labels: `Архитектура`, `Agent Runtime`, `MVP`, `Риск`  
Ответственный агент: `ai-solution-architect`  
Участники: `ai-product-orchestrator`, `ai-system-analyst`, `ai-security-reviewer`, `ai-qa-engineer`  
Приоритет: P0  
Этап: MVP  
Статус: Draft

Цель: утвердить архитектурное решение [ADR-002 Product AI Agents target architecture](../architecture/ADR-002-product-ai-agents-target-architecture.md).

Описание: review показал, что часть Product AI Agents является stage-specific prompt wrappers. Нужно принять или отклонить гибридную модель до production refactor.

Dependencies:

- `docs/architecture/product-ai-agents-architecture-review.md`;
- `docs/architecture/product-ai-agents-target-architecture.md`;
- `docs/architecture/agent-runtime-contract.md`;
- `docs/architecture/simple-retriever-contract.md`;
- `docs/llm-rag/rag-and-retrieval-target-design.md`;
- `BE-02-01`;
- `BE-02-02`.

Acceptance criteria:

- ADR прочитан и принят/отклонён владельцем архитектуры.
- Чётко указано, остаётся ли текущая модель или начинается migration.
- Product AI Agents не смешаны с Global Codex Delivery Agents.
- Corporate wording согласован: единый Agent Runtime с режимами генерации, а не отдельные AI-сервисы.

Definition of Done:

- ADR имеет финальный статус.
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

Title: `ARCH-PA-01 Утвердить ADR по целевой модели Product AI Agents`

Description:

```text
Цель: принять архитектурное решение по целевой модели Product AI Agents в AI Discovery Platform.

Контекст:
- текущие stage agents частично являются prompt wrappers;
- ContextIngestionAgent является отдельным специализированным компонентом;
- RequirementsAgent уже переиспользуется для нескольких artifact types;
- рекомендуемая модель: единый Agent Runtime + ContextIngestionAgent + StageDraftProcessor + RequirementsProcessor + CriticAgent.

Source docs:
- docs/architecture/product-ai-agents-architecture-review.md
- docs/architecture/product-ai-agents-target-architecture.md
- docs/architecture/ADR-002-product-ai-agents-target-architecture.md
- docs/backlog/product-ai-agents-architecture-decision-backlog.md

Responsible agent: ai-solution-architect
Priority: P0
Labels: Архитектура, Agent Runtime, MVP, Риск
Dependencies: BE-02-01, BE-02-02, SimpleRetriever contract, RAG target design

Acceptance criteria:
- ADR принят или отклонён владельцем архитектуры.
- Зафиксировано, нужна ли migration.
- Product AI Agents не смешаны с Global Codex Delivery Agents.
- Corporate wording согласован.

Definition of Done:
- ADR status обновлён.
- Backlog/Gantt отражают решение.
- Production-код не менялся в рамках decision task.
```

Checklist:

- Прочитать architecture review.
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

- API/UI синхронизация Trello не выполнялась.
- Этот файл является manual import package.
- Нельзя утверждать, что карточки созданы на доске, пока пользователь не перенесёт их вручную или не будет подключен Trello API.

