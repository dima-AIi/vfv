import uuid
from datetime import UTC, datetime
from typing import Any


def new_request_id() -> str:
    return str(uuid.uuid4())


class AppError(Exception):
    status_code = 500
    code = "INTERNAL_ERROR"

    def __init__(
        self,
        message: str,
        *,
        code: str | None = None,
        status_code: int | None = None,
        details: list[dict[str, Any]] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        if code is not None:
            self.code = code
        if status_code is not None:
            self.status_code = status_code
        self.details: list[dict[str, Any]] = details or []


class NotFoundError(AppError):
    status_code = 404
    code = "NOT_FOUND"


class ValidationError(AppError):
    status_code = 422
    code = "VALIDATION_ERROR"


class ConflictError(AppError):
    status_code = 409
    code = "CONFLICT"


def build_error_payload(
    error: AppError,
    request_id: str | None = None,
) -> dict[str, Any]:
    return {
        "error": {
            "code": error.code,
            "message": error.message,
            "details": error.details,
            "requestId": request_id or new_request_id(),
            "timestamp": datetime.now(UTC).isoformat(),
        }
    }
