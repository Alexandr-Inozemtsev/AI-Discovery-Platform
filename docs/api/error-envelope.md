# Backend error envelope

Дата: 2026-05-21  
Backlog task: `BE-01-02`  
Статус: реализовано для основного scope MVP error paths.

## Назначение

Документ фиксирует единый формат backend-ошибок AI Discovery Platform. Формат нужен для стабильного frontend parsing, QA regression, security review и дальнейшего OpenAPI hardening.

## Формат envelope

```json
{
  "ok": false,
  "error_code": "PROJECT_NOT_FOUND",
  "human_message": "Проект не найден.",
  "details": {},
  "trace_id": null
}
```

Правила:

- `ok` всегда `false`.
- `error_code` стабильный и машинно-читаемый.
- `human_message` всегда на русском языке.
- `details` содержит только безопасные диагностические данные.
- `trace_id` зарезервирован для будущей observability/telemetry.

## Каталог error codes

| Error code | HTTP status | Назначение | User-facing message |
|---|---:|---|---|
| `PROJECT_NOT_FOUND` | 404 | Проект не найден. | Проект не найден. |
| `ARTIFACT_NOT_FOUND` | 404 | Артефакт не найден. | Артефакт не найден. |
| `UNSUPPORTED_ARTIFACT_TYPE` | 400 | Генерация для artifact type не поддерживается. | Генерация для этого типа артефакта не поддерживается. |
| `LLM_NOT_READY` | 400 | LLM не настроена или не готова к генерации. | LLM не настроена. Откройте настройки LLM и проверьте подключение. |
| `LLM_TIMEOUT` | 400 | Provider timeout. | Превышено время ожидания ответа LLM. |
| `LLM_UNAUTHORIZED` | 400 | Provider вернул 401/403 или authorization error. | Ошибка авторизации LLM provider. Проверьте API key. |
| `LLM_MODEL_NOT_FOUND` | 400 | Модель недоступна. | Модель LLM недоступна или указана неверно. |
| `LLM_INVALID_JSON` | 400 | LLM вернула невалидный JSON/structured response. | LLM вернула некорректный структурированный ответ. |
| `LLM_PROVIDER_ERROR` | 400 | Прочая ошибка provider. | Ошибка LLM provider. |
| `VALIDATION_ERROR` | 400/422 | Некорректные параметры или бизнес-валидация. | Некорректные параметры запроса. |
| `FILE_TOO_LARGE` | 400 | Файл превышает лимит. | Файл слишком большой. |
| `UNSUPPORTED_FILE_TYPE` | 400 | Формат файла не поддерживается. | Формат файла не поддерживается. |
| `TEXT_EXTRACTION_FAILED` | 400 | Ошибка извлечения текста. | Не удалось извлечь текст из файла. |
| `DOCX_EXPORT_FAILED` | 500 | Ошибка DOCX export. | Не удалось сформировать DOCX. |
| `INTERNAL_ERROR` | 500 | Непредвиденная backend ошибка. | Внутренняя ошибка backend. |

## Примеры

### 404 PROJECT_NOT_FOUND

```json
{
  "ok": false,
  "error_code": "PROJECT_NOT_FOUND",
  "human_message": "Проект не найден.",
  "details": {},
  "trace_id": null
}
```

### 400 LLM_NOT_READY

```json
{
  "ok": false,
  "error_code": "LLM_NOT_READY",
  "human_message": "LLM не настроена. Откройте Настройки → LLM настройки и проверьте подключение.",
  "details": {
    "provider": "openrouter",
    "configured": false,
    "ready_for_generation": false,
    "last_connection_status": "not_configured"
  },
  "trace_id": null
}
```

### 422 VALIDATION_ERROR

```json
{
  "ok": false,
  "error_code": "VALIDATION_ERROR",
  "human_message": "Некорректные параметры запроса.",
  "details": {
    "errors": [
      {
        "loc": ["path", "artifact_type"],
        "msg": "Input should be a valid enum",
        "type": "enum"
      }
    ]
  },
  "trace_id": null
}
```

### 500 INTERNAL_ERROR

```json
{
  "ok": false,
  "error_code": "INTERNAL_ERROR",
  "human_message": "Внутренняя ошибка backend.",
  "details": {},
  "trace_id": null
}
```

## LLM error examples

### LLM_UNAUTHORIZED

Provider raw error мапится в `LLM_UNAUTHORIZED`, если содержит 401/403, authorization или unauthorized признаки. Details очищаются от bearer token, API key и private URL.

```json
{
  "ok": false,
  "error_code": "LLM_UNAUTHORIZED",
  "human_message": "Ошибка авторизации LLM provider. Проверьте API key.",
  "details": {
    "stage": "GOAL",
    "provider": "openrouter",
    "model": "test-model",
    "provider_error": "401 [redacted-credential] at [redacted-url]"
  },
  "trace_id": null
}
```

## Sanitization rules

Backend не должен отдавать во frontend:

- API keys;
- bearer tokens;
- authorization headers;
- private provider endpoints/base_url;
- полные provider payload;
- stack traces;
- `.env` values;
- credentials.

Текущая реализация:

- удаляет поля `api_key` и `authorization` из `details`;
- редактирует `Authorization: Bearer ...`, `Bearer ...`, `sk-*` secrets;
- редактирует URL;
- ограничивает длинные diagnostic strings до безопасной длины.

## Frontend parsing rules

Frontend parser должен читать:

- новый envelope: `human_message`, `error_code`, `details`;
- legacy FastAPI shape: `detail.human_message`, `detail.error`, строковый `detail`;
- direct `error`;
- сетевые ошибки и fallback message.

Текущий `frontend/src/api/client.ts` уже читает `human_message` на верхнем уровне и `detail.*`, поэтому отдельное изменение frontend не потребовалось.

## Backward compatibility notes

- Success responses не менялись.
- Основные endpoint paths не менялись.
- Product AI Agents не подключались как Global Codex Delivery Agents.
- File-level upload errors пока сохраняют текущий success response `{ok:true, sources:[...]}` с безопасными per-file statuses; это нужно сохранить для текущего UI workflow.

