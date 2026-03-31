"""Request middleware — tenant injection and structured request logging."""

import logging
import time
import uuid

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.config import get_settings

logger = structlog.get_logger(__name__)
settings = get_settings()


class TenantMiddleware(BaseHTTPMiddleware):
    """Extracts X-Tenant-Id header and stores it on request.state."""

    async def dispatch(self, request: Request, call_next) -> Response:
        tenant_id = request.headers.get("X-Tenant-Id", settings.DEFAULT_TENANT_ID)
        request.state.tenant_id = tenant_id
        return await call_next(request)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Logs every request with method, path, status, and duration."""

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = str(uuid.uuid4())[:8]
        start = time.perf_counter()

        response = await call_next(request)

        duration_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "request",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            status=response.status_code,
            duration_ms=round(duration_ms, 1),
            tenant_id=getattr(request.state, "tenant_id", None),
        )
        return response
