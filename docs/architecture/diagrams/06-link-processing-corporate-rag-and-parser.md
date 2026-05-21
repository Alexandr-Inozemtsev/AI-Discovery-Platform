# 06. Обработка ссылок через Corporate RAG и Universal Parser

## Назначение

Схема фиксирует target design для backlog issue `#75`: обработка ссылок в контексте через Corporate RAG и Universal Link Parser.

```mermaid
flowchart TB
    URL["URL в Context stage"] --> SEC["Security controls\nallowed protocols / SSRF protection"]
    SEC --> A["Сценарий A: Corporate RAG"]
    SEC --> B["Сценарий B: Universal Link Parser"]

    A --> CRC["CorporateRagConnector"]
    CRC --> CRAG["Corporate RAG"]
    CRAG --> CHUNKA["chunks + metadata"]
    CHUNKA --> CTXA["Context Artifact"]

    B --> ULP["UniversalLinkParser"]
    ULP --> FETCH["HTML fetch"]
    FETCH --> MAIN["Main text extraction"]
    FETCH --> ATT["Attachments discovery"]
    ATT --> ALLOW["Attachment allowlist"]
    ALLOW --> ATEXT["Attachment text extraction"]
    MAIN --> CHUNKB["chunks"]
    ATEXT --> CHUNKB
    CHUNKB --> CTXB["Context Artifact"]

    SEC --> BLOCK["Blocked private IP\nno executable files\nfile size limits\nno archive parsing on MVP"]
```

## Security controls

- SSRF protection.
- Allowed protocols: `https` и approved `http` only для внутренних trusted сетей.
- Blocked private IP и loopback targets для public parser mode.
- File size limits для HTML и attachments.
- Attachment allowlist: txt, md, csv, docx, pdf, xlsx.
- No executable files.
- No archive parsing on MVP.

## Связанные документы

- [RAG/retrieval target design](../../llm-rag/rag-and-retrieval-target-design.md)
- [SimpleRetriever Contract](../simple-retriever-contract.md)
- [ТЗ](../../system/tz-ai-discovery-platform-target.md)
- [Security requirements](../../security/security-requirements.md)

## Затронутые backlog/epics

Issue #75, ЭПИК-02, ЭПИК-04, ЭПИК-09, ЭПИК-12, BE-03-01.

