# Чеклист безопасности MCP

Дата: 2026-07-08  
Статус: draft contract

## Обязательные правила

- В repository нельзя сохранять реальные токены, cookies, `.env`, bearer credentials, MCP credentials и приватные URLs.
- MCP config в docs содержит только placeholders вида `{env:CORP_MCP_TOKEN}`, `{env:CONFLUENCE_MCP_URL}`, `{env:JIRA_MCP_URL}`.
- MVP режим для Confluence, Jira, Git и RAG - read-only.
- Запрещённые tool actions: `confluence.write`, `jira.write`, `git.write`, `git.push`, `mcp.credentials.read`, `credential.read`.
- `metadata_only` source не считается evidence.
- Logs/tool_runs/audit должны хранить только safe summary: tool, adapter, status, source_id, source_type, content_level, chunks_count.
- Полный текст корпоративных документов, chunks и extracted_text нельзя писать в audit log.
- Ошибки adapter/MCP не должны возвращать пользователю provider secrets, raw headers или internal stack с credentials.

## Перед подключением реального MCP/MSP

- Проверить allowlist tool actions в `ToolPolicy`.
- Проверить, что adapter не принимает credentials из user payload.
- Проверить redaction для headers: `Authorization`, `Cookie`, `X-API-Key`.
- Проверить rate limits и timeout на adapter layer.
- Проверить, что source_trace сохраняет только идентификаторы источников/chunks, а не полный текст.
- Проверить, что `.env`, local config и MCP credentials находятся в `.gitignore`.
