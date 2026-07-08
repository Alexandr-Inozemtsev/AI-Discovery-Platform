# Контракт Corporate Tool Gateway

Дата: 2026-07-08  
Статус: draft contract

## Назначение

`CorporateToolGateway` - безопасная backend boundary для будущего переиспользования MCP/MSP серверов коллеги. Gateway принимает tool request от AI Discovery Chat orchestration layer, проверяет `ToolPolicy`, вызывает read-only adapter, нормализует ответ в `CorporateSource` и пишет только безопасную audit-сводку.

Gateway не хранит и не возвращает credentials.

## CorporateSource

```json
{
  "source_id": "",
  "source_type": "confluence_page|jira_issue|git_file|rag_chunk|document|link",
  "source_name": "",
  "url": "",
  "content_level": "chunks|extracted_text|metadata_only",
  "text_extraction_status": "completed|failed|metadata_only|unsupported",
  "extracted_text": "",
  "chunks": [],
  "metadata": {},
  "access_scope": "",
  "source_trace": []
}
```

`metadata` проходит sanitization: ключи `api_key`, `authorization`, `cookie`, `credential`, `password`, `secret`, `token` не возвращаются наружу.

## Evidence policy

Источник считается evidence только если:

- `content_level` не равен `metadata_only`;
- `text_extraction_status` равен `completed`;
- для `chunks` есть хотя бы один chunk;
- для `extracted_text` есть непустой extracted text.

`metadata_only` source можно показывать как источник для навигации, но нельзя использовать как подтверждение вывода AI.

## Adapter boundary

Пакет:

```text
discovery-ai-agent/backend/app/corporate_sources/
  corporate_source.py
  corporate_tool_gateway.py
  mcp_gateway.py
  adapters/
    confluence_adapter.py
    jira_adapter.py
    git_adapter.py
    rag_adapter.py
```

Adapters должны реализовать read/search contract:

- `search(request) -> list[CorporateSource]`;
- `read(request) -> CorporateSource | None`.

В MVP adapters не выполняют write operations.

## Safe audit summary

Разрешено логировать:

- tool name;
- adapter name;
- status;
- `query_present`, но не raw query при риске приватных данных;
- `source_id`, `source_type`, `content_level`, `text_extraction_status`, `chunks_count`.

Запрещено логировать:

- bearer tokens, cookies, API keys;
- full extracted text;
- full chunks text;
- raw corporate document body;
- MCP credentials.
