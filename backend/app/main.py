"""SceneDiff FastAPI application entry point.

Responsibilities:
- Create the FastAPI application instance via the factory function.
- Register versioned API routers.
- Attach middleware (CORS, RequestID).
- Configure lifespan startup / shutdown hooks.

No business logic lives here.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import router as api_router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.middleware.request_id import RequestIDMiddleware


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncGenerator[None, None]:
    """Configure resources on startup and release them on shutdown."""
    settings = get_settings()
    configure_logging(settings.LOG_LEVEL)
    # Future: initialise connection pool, warm caches, etc.
    yield
    # Future: gracefully close connection pool, flush buffers, etc.


def create_app() -> FastAPI:
    """Application factory — returns a fully configured FastAPI instance."""
    settings = get_settings()

    application = FastAPI(
        title="SceneDiff",
        version="0.1.0",
        description="AI-powered runtime behavior diff platform.",
        lifespan=lifespan,
        docs_url="/docs" if settings.DOCS_ENABLED else None,
        redoc_url="/redoc" if settings.DOCS_ENABLED else None,
    )

    # --- Middleware (outermost first) ----------------------------------------
    # CORS must be added before RequestID so it applies to preflight responses.
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins_list,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.add_middleware(RequestIDMiddleware)

    # --- Routers ---------------------------------------------------------------
    application.include_router(api_router)

    return application


app = create_app()
