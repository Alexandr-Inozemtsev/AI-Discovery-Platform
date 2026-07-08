# Corporate Tool Gateway: MCP/MSP boundary requirements

Дата: 2026-07-08

## Назначение

Corporate Tool Gateway — будущая граница между AI Discovery Platform и корпоративными источниками знаний, инструментами и model service providers. Он не заменяет FastAPI/React runtime и не становится владельцем Discovery workflow. Его задача — безопасно выдавать ограниченный retrieval/tool result, пригодный для `SimpleRetriever`, `ChatContextAssembler` и Product AI Agents.

## Термины

- MCP boundary — граница вызова корпоративных tools/connectors: поиск по knowledge base, чтение разрешённых документов, получение chunks, metadata и diagnostics.
- MSP boundary — граница model service provider: корпоративный LLM endpoint или OpenAI-compatible provider, который принимает уже собранный prompt context.
- Product AI Agents — агенты внутри AI Discovery Platform, которые работают с Discovery artifacts.
- Global Codex Delivery Agents — внешняя delivery/engineering orchestration layer; не должна смешиваться с Product AI Agents.

## Архитектурные правила

1. FastAPI остаётся единственной backend runtime-точкой AI Discovery Platform.
2. Corporate Tool Gateway не пишет напрямую в `discovery_artifacts`.
3. Любой результат gateway попадает в артефакт только через `proposed_patch` → preview/diff → apply.
4. Gateway возвращает только разрешённые chunks и metadata, а не полный корпус документов.
5. Metadata-only sources не являются evidence.
6. Если evidence отсутствует, downstream agent обязан вернуть `assumptions` и `open_questions`.
7. Gateway не получает secrets из LLM settings, `.env`, cookies, токены Codex или MCP credentials в prompt/log payload.

## MCP tool result contract

Минимальный ответ MCP/tool connector:

```json
{
  "ok": true,
  "query": "проблема пролонгации",
  "chunks": [
    {
      "chunk_id": "kb_123:4",
      "source_id": "kb_123",
      "source_type": "corporate_kb",
      "source_name": "Регламент пролонгации",
      "text": "Фрагмент разрешённого текста",
      "score": 0.81,
      "content_level": "chunks",
      "metadata": {
        "access_scope": "project",
        "truncated": false
      }
    }
  ],
  "source_trace": [
    {
      "source_id": "kb_123",
      "source_name": "Регламент пролонгации",
      "used": true,
      "content_level": "chunks"
    }
  ],
  "warnings": [],
  "diagnostics": {
    "candidate_count": 12,
    "returned_count": 3,
    "filtered_metadata_only": 2
  }
}
```

## Запрещено возвращать как evidence

- Источники с `content_level=metadata_only`.
- Файлы с failed/unsupported extraction без usable text.
- Полные документы, если запрошены только top-k chunks.
- Сырые credentials, cookies, private endpoints, внутренние stack traces.
- Tool-native objects, которые не приводятся к внутреннему retrieval contract.

## MSP prompt boundary

Перед вызовом LLM provider `ChatContextAssembler` должен включать только:

- project snapshot без secrets;
- summaries нужных artifacts;
- top-k retrieved chunks;
- source trace для citations;
- readiness/coverage diagnostics;
- assumptions/open questions;
- token budget metadata.

Prompt не должен включать:

- полный корпус документов;
- metadata-only source content;
- LLM settings и API keys;
- MCP credentials;
- закрытые runtime logs;
- пользовательские файлы сверх retrieval budget.

## Prompt injection controls

- Текст chunks считается недоверенными данными.
- Инструкции внутри источников не могут менять system/developer policy.
- Требования источника раскрыть secrets, отключить проверки или изменить формат ответа игнорируются.
- При конфликте источника с policy приоритет у policy.

## Observability

Разрешённые diagnostics:

- trace id;
- tool name;
- query hash или короткий query summary;
- returned chunk count;
- filtered source count;
- latency;
- warnings;
- token/char budget usage.

Запрещено логировать:

- полный prompt с документами;
- полный текст документов;
- secrets и authorization headers;
- приватные connector endpoints без redaction.

## Quality gates

- Unit tests на metadata-only exclusion.
- Unit tests на prompt budget.
- Unit tests на evidence propagation.
- Security review перед подключением реальных корпоративных connectors.
- Явный fallback на `SimpleRetriever`, если gateway недоступен.

