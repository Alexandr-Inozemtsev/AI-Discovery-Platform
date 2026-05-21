# 02. C4 Container

## Назначение

Схема показывает основные контейнеры текущего MVP и целевого corporate-контура.

```mermaid
flowchart TB
    FE["React/Vite frontend\nСейчас"] --> API["FastAPI backend\nСейчас"]
    API --> DB["SQLite/local DB\nСейчас"]
    API -. target .-> CDB["Corporate DB\nTarget"]
    API --> ART["Artifact Repository\nСейчас"]
    API --> RT["Agent Runtime\nСейчас + target hardening"]
    RT --> CIA["ContextIngestionAgent\nСейчас"]
    RT --> DA["Discovery Agents\nProblem / Goal / Requirements\nСейчас"]
    RT --> RET["SimpleRetriever\nTarget"]
    API --> EXT["File/Text Extraction Service\nСейчас"]
    API --> DOCX["DOCX Export Service\nСейчас"]
    API --> LLMSET["LLM Settings / LLM Gateway\nСейчас"]
    LLMSET --> LLM["OpenRouter / Mock LLM\nСейчас"]
    LLMSET -. corporate .-> CLLM["Corporate LLM\nTarget"]
    RET -. future .-> CRAG["CorporateRagConnector\nFuture optional"]
    EXT -. future .-> ULP["UniversalLinkParser\nFuture optional"]
    CRAG --> CRAGSYS["Corporate RAG\nTarget"]
    ULP --> WEB["Confluence / web / attachments\nTarget"]
```

## Пояснение блоков

- `Сейчас` - уже присутствует в MVP или current docs.
- `Target` - целевой промышленный контур.
- `Future optional` - расширение после security/design approval.

## Связанные документы

- [Target architecture](../target-architecture.md)
- [Agent Runtime Contract](../agent-runtime-contract.md)
- [SimpleRetriever Contract](../simple-retriever-contract.md)
- [Current OpenAPI contract](../../api/openapi-contracts-current.md)

## Затронутые backlog/epics

ЭПИК-02, ЭПИК-03, ЭПИК-04, ЭПИК-08, ЭПИК-09, ЭПИК-11, ЭПИК-12, Issue #75.

