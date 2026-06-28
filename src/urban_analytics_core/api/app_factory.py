"""
FastAPI app factory — shared by all urban analytics projects.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Callable

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp

from urban_analytics_core.settings.base import BaseAppSettings

logger = logging.getLogger(__name__)


# ─── Middleware ───


class TtlResponseCacheMiddleware(BaseHTTPMiddleware):
    """Simple in-memory TTL response cache for GET requests."""

    def __init__(
        self,
        app: ASGIApp,
        ttl_seconds: float = 60.0,
        include_paths: tuple[str, ...] = (),
        max_size: int = 100,
    ) -> None:
        super().__init__(app)
        self._ttl = ttl_seconds
        self._include = set(include_paths)
        self._cache: dict[str, tuple[float, Any]] = {}
        self._max_size = max_size

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Any:
        if request.method != "GET" or not self._include:
            return await call_next(request)

        path = request.url.path
        if not any(path.startswith(p) for p in self._include):
            return await call_next(request)

        import time

        now = time.time()
        entry = self._cache.get(path)
        if entry and (now - entry[0]) < self._ttl:
            return entry[1]

        response = await call_next(request)

        # Only cache successful responses
        if response.status_code == 200 and len(self._cache) < self._max_size:
            self._cache[path] = (now, response)

        return response


class SimpleRateLimitMiddleware(BaseHTTPMiddleware):
    """Per-IP sliding window rate limiter."""

    def __init__(
        self,
        app: ASGIApp,
        window_seconds: float = 60.0,
        max_requests: int = 60,
        include_paths: tuple[str, ...] = (),
    ) -> None:
        super().__init__(app)
        self._window = window_seconds
        self._max = max_requests
        self._include = set(include_paths)
        self._requests: dict[str, list[float]] = {}

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Any:
        path = request.url.path
        if not self._include or not any(
            path.startswith(p) for p in self._include
        ):
            return await call_next(request)

        import time

        ip = request.client.host if request.client else "unknown"
        now = time.time()
        times = self._requests.setdefault(ip, [])

        # Prune old entries
        cutoff = now - self._window
        self._requests[ip] = [t for t in times if t > cutoff]

        if len(self._requests[ip]) >= self._max:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded"},
            )

        self._requests[ip].append(now)
        return await call_next(request)


# ─── App Factory ───


def create_app(
    settings: BaseAppSettings,
    *,
    title: str | None = None,
    version: str = "0.1.0",
    web_dir: str | Path | None = None,
    extra_routes: list | None = None,
    extra_middlewares: list | None = None,
) -> FastAPI:
    """
    Create a standardized FastAPI application.

    Args:
        settings:        Project settings (must inherit BaseAppSettings)
        title:           API title (defaults to app_name)
        version:         API version
        web_dir:         Path to static web frontend
        extra_routes:    List of APIRouter instances to include
        extra_middlewares: List of (middleware_class, **kwargs) tuples
    """
    app = FastAPI(
        title=title or settings.app_name,
        version=version,
    )

    # ── Health check ──
    @app.get("/healthz")
    def healthz() -> dict[str, bool]:
        return {"ok": True}

    # ── CORS ──
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.api.cors.allow_origins,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Response cache ──
    if settings.api.cache.enabled:
        app.add_middleware(
            TtlResponseCacheMiddleware,
            ttl_seconds=float(settings.api.cache.ttl_seconds),
        )

    # ── Rate limiting ──
    if settings.api.rate_limit.enabled:
        app.add_middleware(
            SimpleRateLimitMiddleware,
            window_seconds=float(settings.api.rate_limit.window_seconds),
            max_requests=int(settings.api.rate_limit.max_requests),
        )

    # ── Extra middlewares ──
    if extra_middlewares:
        for mw_cls, kwargs in extra_middlewares:
            app.add_middleware(mw_cls, **kwargs)

    # ── Extra routes ──
    if extra_routes:
        for router in extra_routes:
            app.include_router(router)

    # ── Static web frontend ──
    if web_dir:
        web_path = Path(web_dir)
        if web_path.is_dir():
            app.mount("/static", StaticFiles(directory=str(web_path)), name="static")

            index = web_path / "index.html"
            if index.exists():

                @app.get("/")
                def serve_index() -> FileResponse:
                    return FileResponse(str(index))

    return app
