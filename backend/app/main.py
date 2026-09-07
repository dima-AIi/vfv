from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response as StarletteResponse

from app.core.config import settings
from app.core.context import reset_current_request_id, set_current_request_id
from app.core.errors import AppError, build_error_payload, new_request_id
from app.modules.ai.router import router as ai_router
from app.modules.audit.router import router as audit_router
from app.modules.comments.router import router as comments_router
from app.modules.crm.router import router as crm_router
from app.modules.dashboard.router import router as dashboard_router
from app.modules.documents.router import router as documents_router
from app.modules.files.router import router as files_router
from app.modules.identity.router import router as identity_router
from app.modules.notifications.router import router as notifications_router
from app.modules.notifications.subscribers import register_notification_subscribers
from app.modules.organizations.router import router as organizations_router
from app.modules.projects.router import router as projects_router
from app.modules.search.router import router as search_router
from app.modules.settings.router import router as settings_router
from app.modules.tasks.router import router as tasks_router

API_PREFIX = "/api/v1"

MAX_REQUEST_ID_LENGTH = 200


def resolve_request_id(request: Request) -> str:
    for header in ("x-request-id", "x-correlation-id"):
        raw = request.headers.get(header)
        if raw is None:
            continue
        candidate = raw.strip()
        if not candidate or len(candidate) > MAX_REQUEST_ID_LENGTH:
            continue
        if any(char.isspace() or ord(char) < 32 or ord(char) > 126 for char in candidate):
            continue
        return candidate
    return new_request_id()


class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[StarletteResponse]],
    ) -> StarletteResponse:
        request_id = resolve_request_id(request)
        request.state.request_id = request_id
        token = set_current_request_id(request_id)
        try:
            response = await call_next(request)
        finally:
            reset_current_request_id(token)
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Correlation-ID"] = request_id
        return response


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    register_notification_subscribers()
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        lifespan=lifespan,
        docs_url="/docs",
        openapi_url="/openapi.json",
    )

    app.add_middleware(RequestIdMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-Correlation-ID"],
    )

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, error: AppError) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None)
        return JSONResponse(
            status_code=error.status_code,
            content=build_error_payload(error, request_id),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request,
        error: RequestValidationError,
    ) -> JSONResponse:
        internal = AppError(
            "Некорректные данные запроса.",
            code="VALIDATION_ERROR",
            status_code=422,
            details=[
                {"loc": [str(part) for part in item.get("loc", [])],
                 "msg": str(item.get("msg", "")), "type": str(item.get("type", ""))}
                for item in error.errors()
            ],
        )
        request_id = getattr(request.state, "request_id", None)
        return JSONResponse(
            status_code=internal.status_code,
            content=build_error_payload(internal, request_id),
        )

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, error: Exception) -> JSONResponse:
        internal = AppError("Внутренняя ошибка сервера.")
        request_id = getattr(request.state, "request_id", None)
        return JSONResponse(
            status_code=internal.status_code,
            content=build_error_payload(internal, request_id),
        )

    api_prefix = API_PREFIX

    @app.get(f"{api_prefix}/health", tags=["health"])
    async def health() -> dict[str, str]:
        return {"status": "ok", "version": settings.app_version}

    app.include_router(identity_router, prefix=api_prefix)
    app.include_router(organizations_router, prefix=api_prefix)
    app.include_router(projects_router, prefix=api_prefix)
    app.include_router(tasks_router, prefix=api_prefix)
    app.include_router(documents_router, prefix=api_prefix)
    app.include_router(ai_router, prefix=api_prefix)
    app.include_router(dashboard_router, prefix=api_prefix)
    app.include_router(comments_router, prefix=api_prefix)
    app.include_router(files_router, prefix=api_prefix)
    app.include_router(notifications_router, prefix=api_prefix)
    app.include_router(search_router, prefix=api_prefix)
    app.include_router(crm_router, prefix=api_prefix)
    app.include_router(settings_router, prefix=api_prefix)
    app.include_router(audit_router, prefix=api_prefix)

    return app


app = create_app()
