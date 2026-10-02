from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse


class AppError(Exception):
    status_code = 500
    default_detail = "Internal server error"

    def __init__(self, detail: str | None = None) -> None:
        self.detail = detail or self.default_detail
        super().__init__(self.detail)


class BadRequestError(AppError):
    status_code = 400
    default_detail = "Bad request"


class AuthenticationError(AppError):
    status_code = 401
    default_detail = "Authentication required"


class PermissionDeniedError(AppError):
    status_code = 403
    default_detail = "You do not have permission to do this"


class NotFoundError(AppError):
    status_code = 404
    default_detail = "Resource not found"


class ConflictError(AppError):
    status_code = 409
    default_detail = "Resource already exists"


class AgentUnavailableError(AppError):
    status_code = 502
    default_detail = (
        "AI agent is unavailable. Check GROQ_API_KEY and agent dependencies."
    )


async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
    # Same {"detail": ...} shape FastAPI uses, so the frontend needs no changes.
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
