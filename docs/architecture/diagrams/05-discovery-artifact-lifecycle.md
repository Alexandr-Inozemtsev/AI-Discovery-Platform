# 05. Discovery Artifact Lifecycle

## Назначение

Схема показывает жизненный цикл Discovery artifacts от CONTEXT до DOCX export.

```mermaid
flowchart LR
    C["CONTEXT\nsource_trace / readiness"] --> P["PROBLEM"]
    P --> G["GOAL"]
    G --> BE["BUSINESS_EFFECT"]
    BE --> ASIS["AS_IS"]
    ASIS --> TOBE["TO_BE"]
    TOBE --> UC["USE_CASES"]
    UC --> FR["FUNCTIONAL_REQUIREMENTS"]
    FR --> R["RISKS"]
    R --> BT["FINAL_BT"]
    BT --> DOCX["DOCX EXPORT"]

    HITL["Human-in-the-loop\nподтверждение"] -.-> C
    HITL -.-> P
    HITL -.-> G
    VER["Versioning\nartifact.version"] -.-> P
    STALE["Stale dependents\nпосле upstream changes"] -.-> G
    VAL["Validation / CriticAgent"] -.-> BT
    EVID["Evidence\nsource_trace"] -.-> C
    EVID -.-> FR
```

## Пояснение блоков

Каждый artifact сохраняется с version. При изменении upstream artifact downstream stages могут стать stale. AI предлагает, пользователь подтверждает, затем artifact становится входом для следующего этапа.

## Связанные документы

- [ТЗ](../../system/tz-ai-discovery-platform-target.md)
- [Current OpenAPI contract](../../api/openapi-contracts-current.md)
- [Agent Runtime Contract](../agent-runtime-contract.md)

## Затронутые backlog/epics

ЭПИК-01, ЭПИК-05, ЭПИК-06, ЭПИК-07, ЭПИК-08, ЭПИК-11, ЭПИК-15.

