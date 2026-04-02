"""AutoTriage FastAPI application factory."""

import logging
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.config import get_settings
from app.core.exceptions import (
    AutoTriageException,
    ConfigurationError,
    TicketNotFoundError,
    TenantNotFoundError,
    TriageEngineError,
)
from app.core.middleware import RequestLoggingMiddleware, TenantMiddleware
from app.schemas.error import ErrorResponse

logger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# OpenAPI tag metadata
# ---------------------------------------------------------------------------

_TAGS = [
    {"name": "health", "description": "Health and readiness checks"},
    {"name": "tickets", "description": "Ticket creation, listing, and retrieval"},
    {"name": "triage", "description": "Re-triage and triage version history"},
    {"name": "feedback", "description": "Consultant accept/override feedback"},
    {"name": "knowledge-base", "description": "KB article CRUD and semantic search"},
    {"name": "dashboard", "description": "KPI metrics and accuracy reporting"},
    {"name": "admin", "description": "Tenant configuration and model version management"},
]

# ---------------------------------------------------------------------------
# Exception → ErrorResponse + HTTP status mapping
# ---------------------------------------------------------------------------

_EXCEPTION_MAP: dict[type, tuple[int, str]] = {
    TicketNotFoundError:   (status.HTTP_404_NOT_FOUND,           "TICKET_NOT_FOUND"),
    TenantNotFoundError:   (status.HTTP_404_NOT_FOUND,           "TENANT_NOT_FOUND"),
    TriageEngineError:     (status.HTTP_502_BAD_GATEWAY,         "TRIAGE_FAILED"),
    ConfigurationError:    (status.HTTP_500_INTERNAL_SERVER_ERROR, "CONFIGURATION_ERROR"),
    AutoTriageException:   (status.HTTP_500_INTERNAL_SERVER_ERROR, "INTERNAL_ERROR"),
}


def _error_response(exc: AutoTriageException, code: str) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=type(exc).__name__,
            detail=exc.message,
            code=code,
        ).model_dump(),
    )


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(_app: FastAPI):
    logging.basicConfig(level=get_settings().LOG_LEVEL)
    logger.info("AutoTriage API starting up")
    try:
        from app.database import engine
        async with engine.connect() as conn:
            await conn.execute(__import__("sqlalchemy").text("SELECT 1"))
        logger.info("Database connection verified")
    except Exception as exc:
        logger.warning("Database not reachable at startup", error=str(exc))
    logger.info("AutoTriage API ready")
    yield
    logger.info("AutoTriage API shutting down")


# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------

def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="AutoTriage API",
        version="0.1.0",
        description=(
            "AI-powered SAP incident triage platform. "
            "Classifies support tickets by module and priority using Claude, "
            "enriches them with similar tickets and KB articles, and applies "
            "configurable rule overrides."
        ),
        openapi_tags=_TAGS,
        lifespan=lifespan,
        responses={
            422: {"description": "Validation Error"},
            500: {"model": ErrorResponse, "description": "Internal Server Error"},
        },
    )

    # CORS — configurable via CORS_ORIGINS env var
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(TenantMiddleware)

    app.include_router(api_router)

    @app.get("/", tags=["health"])
    async def root():
        return {"status": "ok", "version": "0.1.0"}

    # ---------------------------------------------------------------------------
    # Exception handlers — most specific first
    # ---------------------------------------------------------------------------

    @app.exception_handler(TicketNotFoundError)
    async def ticket_not_found_handler(_req: Request, exc: TicketNotFoundError):
        return _error_response(exc, "TICKET_NOT_FOUND")

    @app.exception_handler(TenantNotFoundError)
    async def tenant_not_found_handler(_req: Request, exc: TenantNotFoundError):
        return _error_response(exc, "TENANT_NOT_FOUND")

    @app.exception_handler(TriageEngineError)
    async def triage_engine_handler(_req: Request, exc: TriageEngineError):
        return _error_response(exc, "TRIAGE_FAILED")

    @app.exception_handler(ConfigurationError)
    async def config_error_handler(_req: Request, exc: ConfigurationError):
        return _error_response(exc, "CONFIGURATION_ERROR")

    @app.exception_handler(AutoTriageException)
    async def autotriage_handler(_req: Request, exc: AutoTriageException):
        code = type(exc).__name__.upper().replace("ERROR", "_ERROR").rstrip("_ERROR") + "_ERROR"
        return _error_response(exc, code)

    return app


app = create_app()
