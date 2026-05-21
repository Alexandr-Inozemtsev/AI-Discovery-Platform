from typing import Any

from pydantic import BaseModel, Field


class ErrorEnvelope(BaseModel):
    ok: bool = False
    error_code: str
    human_message: str
    details: dict[str, Any] = Field(default_factory=dict)
    trace_id: str | None = None

