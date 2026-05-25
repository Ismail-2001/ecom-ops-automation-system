import uuid
import logging
from typing import Callable
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseMiddleware

from ecommerce_ops.config import settings, Environment

logger = logging.getLogger("ecommerce_ops.api.middleware")


class RequestIDMiddleware(BaseMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


class RequestLoggingMiddleware(BaseMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = getattr(request.state, "request_id", "unknown")
        logger.info(
            "Request started: %s %s [%s]", request.method, request.url.path, request_id
        )
        response = await call_next(request)
        logger.info(
            "Request completed: %s %s -> %s [%s]",
            request.method, request.url.path, response.status_code, request_id,
        )
        return response


def setup_middleware(app: FastAPI):
    if settings.ENV == Environment.PRODUCTION:
        allowed_origins = settings.CORS_ORIGINS
    else:
        allowed_origins = ["*"]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(RequestLoggingMiddleware)
