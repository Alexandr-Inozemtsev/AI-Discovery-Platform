import re
from typing import Any

from fastapi import HTTPException


MAX_DETAIL_LENGTH = 500


DEFAULT_MESSAGES = {
    "PROJECT_NOT_FOUND": "Проект не найден.",
    "ARTIFACT_NOT_FOUND": "Артефакт не найден.",
    "UNSUPPORTED_ARTIFACT_TYPE": "Генерация для этого типа артефакта не поддерживается.",
    "LLM_NOT_READY": "LLM не настроена. Откройте настройки LLM и проверьте подключение.",
    "LLM_TIMEOUT": "Превышено время ожидания ответа LLM.",
    "LLM_UNAUTHORIZED": "Ошибка авторизации LLM provider. Проверьте API key.",
    "LLM_MODEL_NOT_FOUND": "Модель LLM недоступна или указана неверно.",
    "LLM_INVALID_JSON": "LLM вернула некорректный структурированный ответ.",
    "LLM_PROVIDER_ERROR": "Ошибка LLM provider.",
    "VALIDATION_ERROR": "Некорректные параметры запроса.",
    "FILE_TOO_LARGE": "Файл слишком большой.",
    "UNSUPPORTED_FILE_TYPE": "Формат файла не поддерживается.",
    "TEXT_EXTRACTION_FAILED": "Не удалось извлечь текст из файла.",
    "DOCX_EXPORT_FAILED": "Не удалось сформировать DOCX.",
    "INTERNAL_ERROR": "Внутренняя ошибка backend.",
}


def sanitize_error_detail(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, dict):
        return {str(k): sanitize_error_detail(v) for k, v in value.items() if str(k).lower() not in {"api_key", "authorization"}}
    if isinstance(value, list):
        return [sanitize_error_detail(v) for v in value[:20]]
    if isinstance(value, (bool, int, float)):
        return value
    text = str(value)
    text = re.sub(r"Authorization\s*:\s*Bearer\s+[^\s,;]+", "[redacted-credential]", text, flags=re.IGNORECASE)
    text = re.sub(r"Bearer\s+[^\s,;]+", "[redacted-credential]", text, flags=re.IGNORECASE)
    text = re.sub(r"\bsk-[A-Za-z0-9_\-]+", "[redacted-secret]", text)
    text = re.sub(r"https?://[^\s,;)]+", "[redacted-url]", text, flags=re.IGNORECASE)
    if len(text) > MAX_DETAIL_LENGTH:
        return text[:MAX_DETAIL_LENGTH].rstrip() + "...[truncated]"
    return text


def error_envelope(
    error_code: str,
    human_message: str | None = None,
    details: dict[str, Any] | None = None,
    trace_id: str | None = None,
) -> dict[str, Any]:
    return {
        "ok": False,
        "error_code": error_code,
        "human_message": human_message or DEFAULT_MESSAGES.get(error_code, DEFAULT_MESSAGES["INTERNAL_ERROR"]),
        "details": sanitize_error_detail(details or {}),
        "trace_id": trace_id,
    }


def api_error(
    status_code: int,
    error_code: str,
    human_message: str | None = None,
    details: dict[str, Any] | None = None,
    trace_id: str | None = None,
) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail=error_envelope(error_code, human_message=human_message, details=details, trace_id=trace_id),
    )


def infer_llm_error_code(raw_error: Any) -> str:
    text = str(raw_error or "").lower()
    if "401" in text or "403" in text or "unauthorized" in text or "authorization" in text:
        return "LLM_UNAUTHORIZED"
    if "timeout" in text or "timed out" in text:
        return "LLM_TIMEOUT"
    if "model" in text and ("not found" in text or "does not exist" in text):
        return "LLM_MODEL_NOT_FOUND"
    return "LLM_PROVIDER_ERROR"


def llm_api_error(
    raw_error: Any,
    *,
    stage: str,
    provider: str,
    model: str,
    human_message: str | None = None,
) -> HTTPException:
    code = infer_llm_error_code(raw_error)
    return api_error(
        400,
        code,
        human_message=human_message or DEFAULT_MESSAGES[code],
        details={
            "stage": stage,
            "provider": provider,
            "model": model,
            "provider_error": sanitize_error_detail(raw_error),
        },
    )
