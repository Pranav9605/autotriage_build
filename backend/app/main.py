"""AutoTriage FastAPI application factory."""

import logging

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.core.exceptions import AutoTriageException
from app.core.middleware import RequestLoggingMiddleware, TenantMiddleware

logger = structlog.get_logger(__name__)


def create_app() -> FastAPI:
    app = FastAPI(
        title="AutoTriage API",
        version="0.1.0",
        description="AI-powered SAP incident triage platform",
    )

    # CORS — allow all origins for POC
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Request logging must be outermost so it captures all requests
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(TenantMiddleware)

    # Routes
    app.include_router(api_router)

    # Keep the original root health check
    @app.get("/", tags=["root"])
    async def root():
        return {"status": "ok"}

    # Exception handlers
    @app.exception_handler(AutoTriageException)
    async def autotriage_exception_handler(
        _request: Request, exc: AutoTriageException
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.message},
        )

    @app.on_event("startup")
    async def on_startup():
        logging.basicConfig(level=logging.INFO)
        logger.info("AutoTriage API started")

    return app


app = create_app()
