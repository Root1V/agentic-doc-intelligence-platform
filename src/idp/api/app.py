"""FastAPI app factory."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from opentelemetry import trace

from idp.api.routes import batches, documents, review, type_suggestions
from idp.config import get_settings
from idp.observability.otel import setup_tracing
from idp.storage.object_store import S3ObjectStore


def create_app() -> FastAPI:
    settings = get_settings()
    setup_tracing(settings)

    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
        S3ObjectStore(settings).ensure_bucket()
        yield
        # BatchSpanProcessor buffers spans and exports on a timer — without
        # this, spans from requests near process shutdown can be silently
        # dropped instead of reaching the exporter.
        trace.get_tracer_provider().shutdown()  # type: ignore[union-attr]

    app = FastAPI(title="Intelligent Document Platform", version="0.1.0", lifespan=lifespan)
    app.include_router(batches.router)
    app.include_router(documents.router)
    app.include_router(review.router)
    app.include_router(type_suggestions.router)

    @app.get("/health")
    async def health() -> dict:
        return {"status": "ok"}

    return app


app = create_app()
