from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.errors import DEFAULT_MESSAGES, error_envelope, sanitize_error_detail


def _is_envelope(value) -> bool:
    return isinstance(value, dict) and value.get("ok") is False and "error_code" in value and "human_message" in value


def _code_from_status(status_code: int) -> str:
    if status_code == 422:
        return "VALIDATION_ERROR"
    if status_code == 404:
        return "PROJECT_NOT_FOUND"
    if status_code == 400:
        return "VALIDATION_ERROR"
    return "INTERNAL_ERROR"


async def http_exception_handler(request: Request, exc: HTTPException):
    if _is_envelope(exc.detail):
        return JSONResponse(status_code=exc.status_code, content=exc.detail)
    code = _code_from_status(exc.status_code)
    message = DEFAULT_MESSAGES.get(code, DEFAULT_MESSAGES["INTERNAL_ERROR"])
    return JSONResponse(
        status_code=exc.status_code,
        content=error_envelope(code, message, {"detail": sanitize_error_detail(exc.detail)}),
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = [
        {
            "loc": list(err.get("loc", [])),
            "msg": err.get("msg"),
            "type": err.get("type"),
        }
        for err in exc.errors()
    ]
    return JSONResponse(
        status_code=422,
        content=error_envelope("VALIDATION_ERROR", details={"errors": errors}),
    )


async def unhandled_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content=error_envelope("INTERNAL_ERROR"),
    )


def install_error_handlers(app):
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)

