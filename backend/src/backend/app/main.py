from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.v1.chat import router as chat_router
from backend.app.core.config import Settings, settings
from backend.app.rag.retriever import CatalogRetriever
from backend.app.schemas.chat import CatalogFilterSchema


def create_app(app_settings: Settings = settings) -> FastAPI:
    app = FastAPI(title=app_settings.project_name, version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.state.settings = app_settings
    app.state.retriever = CatalogRetriever(app_settings.catalog_path)
    app.state.default_filters = CatalogFilterSchema
    app.include_router(chat_router, prefix=app_settings.api_v1_prefix)

    @app.get("/health/live", tags=["Health"])
    def liveness() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/health/ready", tags=["Health"])
    def readiness() -> dict[str, str]:
        status = "ok" if app.state.retriever.exists() else "unavailable"
        return {"status": status}

    return app


app = create_app()
