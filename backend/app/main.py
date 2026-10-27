from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import Engine

from app.core.config import Settings, get_settings
from app.core.database import engine, initialize_database
from app.features.auth.routes import router as auth_router


def create_app(
    settings: Settings | None = None,
    database_engine: Engine | None = None,
) -> FastAPI:
    application_settings = settings or get_settings()
    application_engine = database_engine or engine

    @asynccontextmanager
    async def lifespan(_application: FastAPI) -> AsyncIterator[None]:
        initialize_database(application_engine)
        yield

    application = FastAPI(
        title=application_settings.app_name,
        lifespan=lifespan,
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=application_settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "X-CSRF-Token"],
    )
    application.include_router(auth_router)

    @application.get("/api/health", tags=["health"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return application


app = create_app()
