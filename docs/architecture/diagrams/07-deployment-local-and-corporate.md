# 07. Deployment: local demo и corporate target

## Назначение

Схема показывает два режима deployment: текущий local demo и целевой corporate target.

```mermaid
flowchart LR
    subgraph Local["Local demo / Windows without Docker"]
        LFE["Frontend\nReact/Vite"]
        LBE["Backend\nFastAPI"]
        LDB["SQLite"]
        LLLM["Mock / OpenRouter LLM"]
        LFE --> LBE
        LBE --> LDB
        LBE --> LLLM
    end

    subgraph Corp["Corporate target"]
        CFE["Frontend"]
        CBE["Backend"]
        CDB["Corporate DB"]
        CLLM["Corporate LLM"]
        CRAG["Corporate RAG"]
        IAM["SSO / IAM"]
        AUD["Audit"]
        SFS["Secure file storage"]
        CFE --> CBE
        CBE --> CDB
        CBE --> CLLM
        CBE --> CRAG
        CBE --> IAM
        CBE --> AUD
        CBE --> SFS
    end
```

## Пояснение блоков

Local demo нужен для разработки и демонстраций без Docker. Corporate target нужен для production/pilot: SSO, audit, secure storage, corporate DB, corporate LLM и corporate RAG.

## Связанные документы

- [Runbook локального запуска](../../runbook/local-runbook.md)
- [Target architecture](../target-architecture.md)
- [Security requirements](../../security/security-requirements.md)
- [TЗ](../../system/tz-ai-discovery-platform-target.md)

## Затронутые backlog/epics

ЭПИК-09, ЭПИК-11, ЭПИК-12, ЭПИК-14, ЭПИК-15.

