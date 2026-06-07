"""FastAPI application factory for Agent Canvas."""

from __future__ import annotations

import json

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import api_router
from app.config import settings
from app.schemas.canonical import CanonicalEnvelope


def create_app() -> FastAPI:
    app = FastAPI(
        title="Agent Canvas API",
        version="0.1.0",
        description="Trace ingestion, storage, and query API for Agent Canvas.",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router, prefix=settings.api_prefix)

    @app.get("/healthz", tags=["meta"])
    def healthz() -> dict:
        return {"status": "ok"}

    @app.get(f"{settings.api_prefix}/schema/canonical", tags=["meta"])
    def canonical_schema() -> dict:
        """The canonical envelope JSON Schema, for adapter authors."""
        return json.loads(json.dumps(CanonicalEnvelope.model_json_schema()))

    return app


app = create_app()
