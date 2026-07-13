"""
Database engine and session management.

A single SQLAlchemy engine is created at import time from the
configured DATABASE_URL. `get_db()` is a FastAPI dependency that
yields a Session per request and guarantees it is closed afterward,
including on exceptions.
"""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings

settings = get_settings()

# `connect_args` is only needed for SQLite: it disallows using a
# connection across threads by default, which breaks FastAPI's
# threaded request handling for sync routes. Postgres does not need
# (or accept) this argument.
_connect_args = (
    {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
)

engine = create_engine(
    settings.database_url,
    connect_args=_connect_args,
    pool_pre_ping=True,  # detects stale Postgres connections before use
    echo=settings.debug and settings.environment == "local",
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that provides a database session for the
    lifetime of a single request.

    Usage:
        @router.get("/resumes/{id}")
        def get_resume(id: UUID, db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
