# Архитектурные схемы

Каталог содержит отдельные Mermaid-схемы AI Discovery Platform. Схемы нужны для architecture review, QA, planning, onboarding и презентации руководству.

| Файл | Назначение | Основные источники |
|---|---|---|
| [01-c4-context.md](01-c4-context.md) | C4 Context: пользователи, платформа и внешние системы. | ТЗ, target architecture, backlog |
| [02-c4-container.md](02-c4-container.md) | C4 Container: frontend, backend, DB, runtime, RAG, export. | ТЗ, Agent Runtime Contract |
| [03-agent-runtime-flow.md](03-agent-runtime-flow.md) | Flow генерации через Agent Runtime. | Agent Runtime Contract, SimpleRetriever |
| [04-context-ingestion-and-rag.md](04-context-ingestion-and-rag.md) | Context ingestion, source trace, readiness, downstream stages. | RAG/retrieval target design |
| [05-discovery-artifact-lifecycle.md](05-discovery-artifact-lifecycle.md) | Lifecycle Discovery artifacts и DOCX export. | ТЗ, current API contract |
| [06-link-processing-corporate-rag-and-parser.md](06-link-processing-corporate-rag-and-parser.md) | Issue #75: обработка ссылок через Corporate RAG и Universal Link Parser. | Backlog, RAG target design |
| [07-deployment-local-and-corporate.md](07-deployment-local-and-corporate.md) | Local demo и corporate target deployment. | DevOps docs, target architecture |

## Правила обновления

- Схема обновляется вместе с архитектурным документом, на который она ссылается.
- Если схема меняет delivery scope, обновляются backlog traceability matrix и Gantt.
- Схемы не являются production-кодом и не подключают Global Codex Delivery Agents как backend services.

