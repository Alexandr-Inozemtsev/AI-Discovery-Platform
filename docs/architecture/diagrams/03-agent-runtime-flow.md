# 03. Agent Runtime Flow

## Назначение

Схема фиксирует целевой flow генерации artifact через backend Agent Runtime продукта.

```mermaid
sequenceDiagram
    participant User as Пользователь
    participant FE as Frontend
    participant API as FastAPI backend
    participant RT as AgentOrchestrator
    participant RET as SimpleRetriever
    participant Agent as Product AI Agent
    participant LLM as LLM Provider
    participant Repo as Artifact Repository

    User->>FE: Запускает генерацию
    FE->>API: GET /api/runtime/status
    API-->>FE: LLM readiness
    FE->>API: POST /api/projects/{id}/generate/{artifact_type}
    API->>API: _ensure_llm_ready
    API->>RT: get_agent(artifact_type)
    RT-->>API: выбранный agent
    API->>RET: получить релевантные chunks
    RET-->>API: chunks + source metadata
    API->>Agent: build prompt + context
    Agent->>LLM: generate(prompt)
    alt LLM success
        LLM-->>Agent: result
    else LLM error
        Agent-->>API: fallback / error
    end
    API->>Repo: upsert artifact + version
    Repo-->>API: ArtifactRead
    API-->>FE: result + structured_content/source_trace
```

## Пояснение блоков

`AgentOrchestrator` здесь является product runtime orchestrator внутри backend, а не глобальным Codex delivery agent. `SimpleRetriever` добавляет grounding и source trace для целевого контура.

## Связанные документы

- [Agent Runtime Contract](../agent-runtime-contract.md)
- [SimpleRetriever Contract](../simple-retriever-contract.md)
- [Current OpenAPI contract](../../api/openapi-contracts-current.md)
- [RAG/retrieval target design](../../llm-rag/rag-and-retrieval-target-design.md)

## Затронутые backlog/epics

ЭПИК-03, ЭПИК-04, ЭПИК-05, ЭПИК-07, BE-02-01.

