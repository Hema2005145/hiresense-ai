"""
Application entrypoint.

Creates the FastAPI app via a factory function (`create_app`) rather
than a bare module-level `app = FastAPI()`. The factory pattern makes
the app testable — tests can call `create_app()` with overridden
settings/dependencies instead of importing a single global instance —
and keeps startup/shutdown logic explicit via the lifespan context
manager instead of the deprecated `@app.on_event` decorators.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes.health import router as health_router
from app.config import get_settings
from app.core.exceptions import HireSenseError
from app.core.logging_config import configure_logging
from app.models.base import Base
from app.db.session import engine

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Runs once at startup and once at shutdown.

    Startup: configures logging and creates database tables if they
    don't exist. `Base.metadata.create_all` is intentionally used here
    instead of Alembic migrations for local/dev convenience — Alembic
    migrations are introduced in the deployment phase for production
    schema changes, so this call becomes a no-op once migrations own
    the schema (tables already exist, `create_all` skips them).
    """
    configure_logging()
    settings = get_settings()
    logger.info(
        "Starting %s v%s in %s mode",
        settings.app_name,
        settings.app_version,
        settings.environment,
    )

    # Import models so their tables are registered on Base.metadata
    # before create_all runs. As new model modules are added in later
    # phases, they get imported here too.
    import app.models.base  # noqa: F401

    Base.metadata.create_all(bind=engine)
    logger.info("Database tables ensured.")

    yield

    logger.info("Shutting down %s", settings.app_name)


def create_app() -> FastAPI:
    """Application factory. Builds and returns a configured FastAPI app."""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "HireSense AI — Intelligent Resume Screening & "
            "Interview Assistant API"
        ),
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)
    register_routers(app, settings.api_v1_prefix)
    mount_static_frontend(app)

    return app


def register_exception_handlers(app: FastAPI) -> None:
    """
    Registers a single handler that converts any HireSenseError (and
    its subclasses) into a consistent JSON error envelope, per the
    API convention locked in during Phase 1:

        {"error": {"code": ..., "message": ..., "details": ...}}

    Because every service raises HireSenseError subclasses instead of
    HTTPException, this one handler covers the entire application —
    no route needs its own try/except block for domain errors.
    """

    @app.exception_handler(HireSenseError)
    async def handle_hiresense_error(
        request: Request, exc: HireSenseError
    ) -> JSONResponse:
        logger.warning(
            "%s: %s (path=%s)", exc.error_code, exc.message, request.url.path
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.error_code,
                    "message": exc.message,
                    "details": exc.details,
                }
            },
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(
        request: Request, exc: Exception
    ) -> JSONResponse:
        # Catch-all so an unhandled bug never leaks a raw traceback to
        # the client. Logged with full traceback for debugging; the
        # client only sees a generic message.
        logger.exception("Unhandled exception on %s", request.url.path)
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "internal_error",
                    "message": "An unexpected error occurred.",
                    "details": {},
                }
            },
        )


def register_routers(app: FastAPI, api_prefix: str) -> None:
    """
    Registers all API routers under the versioned prefix.

    As modules are built in later phases, their routers are added
    here — this function becomes the single map of "every route group
    the API exposes".
    """
    app.include_router(health_router, prefix=api_prefix)


def mount_static_frontend(app: FastAPI) -> None:
    """
    Serves the static HTML/CSS/JS frontend directly from FastAPI.

    The frontend is a plain static site (per the chosen architecture:
    static HTML/CSS/Bootstrap/JS calling the REST API), so it needs no
    templating engine — StaticFiles serves it as-is. This keeps local
    development to a single running process (`uvicorn`) instead of
    requiring a separate frontend dev server.
    """
    app.mount(
        "/",
        StaticFiles(directory="../frontend", html=True),
        name="frontend",
    )


app = create_app()
