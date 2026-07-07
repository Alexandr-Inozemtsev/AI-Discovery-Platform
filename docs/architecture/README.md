# Архитектурная документация AI Discovery Platform

## Карта документов

| Документ | Назначение | Статус | Владелец / роль | Когда обновлять |
|---|---|---|---|---|
| [ТЗ целевого состояния](../system/tz-ai-discovery-platform-target.md) | Полный системный scope: функции, API, security, phases, handoff. | Target-state | `ai-system-analyst` | При изменении требований, API, ролей, security или delivery phases. |
| [Целевая архитектура](target-architecture.md) | Верхнеуровневые компоненты и целевой контур платформы. | Target-state | `ai-solution-architect` | При изменении компонентов, интеграций или deployment assumptions. |
| [ADR-001 AI/RAG/agent framework](ADR-001-agent-and-rag-framework-selection.md) | Решение по AI/RAG/framework strategy и ограничениям внешних frameworks. | Architecture decision | `ai-solution-architect` | При пересмотре framework strategy или добавлении внешнего orchestration framework. |
| [ADR-002 target platform evolution](adr-002-target-platform-evolution.md) | Архитектурная эволюция платформы. | Architecture decision | `ai-solution-architect` | При изменении target architecture. |
| [ADR-003 Product AI Agents target architecture](ADR-003-product-ai-agents-target-architecture.md) | Целевая гибридная модель Product AI Agents: Agent Runtime, stage processors, prompt registry, LLM Gateway. | Architecture decision baseline for ADR-004 | `ai-solution-architect` | При изменении Product AI Agents target model, BE-02-05/BE-02-06 или corporate wording. |
| [ADR-004 AI Discovery Chat Architecture](ADR-004-ai-discovery-chat-architecture.md) | Chat-first UX: AI Discovery Chat как единая точка входа, формы этапов как structured state, proposed patch/preview/apply gate. | Architecture decision | `ai-product-orchestrator`, `ai-solution-architect` | При изменении Chat Orchestrator, chat endpoints, patch/apply policy или ToolPolicy. |
| [Chat Orchestrator Contract](chat-orchestrator-contract.md) | Контракт intent routing, ToolPolicy, StageProcessorRequest/Result, preview/apply и QA gates для AI Discovery Chat. | Phase 1 contract | `ai-system-analyst`, `ai-backend-developer` | При изменении chat runtime contract или tool policy. |
| [Product AI Agents architecture review](product-ai-agents-architecture-review.md) | Экспертная оценка текущих Product AI Agents и альтернатив архитектуры. | Current-state review | `ai-solution-architect` | При пересмотре Product AI Agents или Agent Runtime roadmap. |
| [Product AI Agents target architecture](product-ai-agents-target-architecture.md) | Target-state draft по гибридной модели Product AI Agents. | Target-state draft | `ai-solution-architect` | При изменении stage processor contract или prompt governance. |
| [Agent Runtime Contract](agent-runtime-contract.md) | Контракт запуска product AI agents, result, errors, metadata. | Target-state | `ai-solution-architect`, `ai-backend-developer` | При изменении runtime contract или agent result shape. |
| [Agent Runtime Roadmap](agent-runtime-roadmap.md) | План развития product Agent Runtime. | Draft | `ai-solution-architect` | При изменении backend runtime roadmap. |
| [SimpleRetriever Contract](simple-retriever-contract.md) | Контракт retrieval без внешних RAG dependencies. | Target-state | `ai-llm-rag-engineer` | При изменении retrieval boundary, ranking или source trace. |
| [RAG/retrieval target design](../llm-rag/rag-and-retrieval-target-design.md) | Целевая RAG/retrieval архитектура, context grounding, evals. | Target-state | `ai-llm-rag-engineer` | При изменении RAG flow, corporate RAG или provider policy. |
| [Current OpenAPI contract](../api/openapi-contracts-current.md) | Фактический API contract текущего MVP. | Current-state | `ai-system-analyst`, `ai-backend-developer` | При изменении endpoint-ов или response shape. |
| [Архитектурные схемы](diagrams/README.md) | Отдельный каталог Mermaid-схем для разработки и презентаций. | Draft/Target-state | `ai-solution-architect` | При изменении architecture, delivery roadmap или issue #75. |
| [Trello backlog cards](../backlog/trello-cards.md) | Delivery backlog и manual Trello package. | Delivery source | `ai-trello-analyst` | При изменении scope, priority или dependencies. |
| [Gantt delivery plan](../ai-delivery-agents/07-gantt-delivery-plan.md) | Delivery roadmap и Gantt. | Draft | `ai-delivery-project-manager` | При изменении сроков, phases или dependencies. |

## Source of truth

- Для системного scope: [ТЗ целевого состояния](../system/tz-ai-discovery-platform-target.md).
- Для текущего API: [Current OpenAPI contract](../api/openapi-contracts-current.md).
- Для product Agent Runtime: [Agent Runtime Contract](agent-runtime-contract.md), [Product AI Agents architecture review](product-ai-agents-architecture-review.md), [ADR-003 Product AI Agents target architecture](ADR-003-product-ai-agents-target-architecture.md).
- Для retrieval: [SimpleRetriever Contract](simple-retriever-contract.md) и [RAG/retrieval target design](../llm-rag/rag-and-retrieval-target-design.md).
- Для delivery scope: [Trello backlog cards](../backlog/trello-cards.md) и [Gantt delivery plan](../ai-delivery-agents/07-gantt-delivery-plan.md).

## Архитектурные решения

Главные решения зафиксированы в ADR. `ADR-001` ограничивает преждевременное подключение LangGraph, LlamaIndex и Haystack как foundation. `ADR-002` сохраняет решение по target platform evolution. `ADR-003` фиксирует целевую модель Product AI Agents и устраняет конфликт нумерации по этому решению. `ADR-004` фиксирует chat-first UX: AI Discovery Chat становится единой точкой входа, но изменения артефактов идут только через `proposed_patch -> preview -> apply`.

## Runtime и agents

Product AI Agents живут в backend runtime продукта и не смешиваются с Global Codex Delivery Agents. Runtime-контур описан в [Agent Runtime Contract](agent-runtime-contract.md), roadmap - в [Agent Runtime Roadmap](agent-runtime-roadmap.md), целевая модель - в [ADR-003](ADR-003-product-ai-agents-target-architecture.md), chat-first orchestration - в [ADR-004](ADR-004-ai-discovery-chat-architecture.md) и [Chat Orchestrator Contract](chat-orchestrator-contract.md).

## RAG / Retrieval

RAG-контур описывает ручной контекст, файлы, ссылки, chunks, source trace, coverage, readiness и future corporate RAG. Новая задача `Issue #75` по ссылкам отражена в [схеме обработки ссылок](diagrams/06-link-processing-corporate-rag-and-parser.md), [traceability matrix](../backlog/backlog-traceability-matrix.md) и Gantt v2.

## Delivery / backlog

Delivery planning ведется через backlog, Trello package и Gantt. Эти документы не являются runtime-кодом и используются глобальными Codex delivery agents как рабочий контур разработки.

## Design / UI

Дизайн-документация находится в [docs/design](../design/README.md). Основной source of truth: screen inventory, design system, context screen spec, coded prototype/screenshots при наличии.

## Management presentation assets

Материалы для руководства находятся в [docs/presentations](../presentations/management-platform-overview.md). Figma Slides handoff описан в [figma-use-slides brief](../presentations/figma-use-slides-brief.md).
