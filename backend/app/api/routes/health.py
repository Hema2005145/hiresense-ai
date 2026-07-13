"""
Health check endpoint.

Used by Docker healthchecks, load balancers, and deployment platforms
(Render/Railway) to verify the service is up and can reach its
database.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.db.session import get_db

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check(
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict:
    """
    Returns service status and confirms database connectivity.

    Deliberately does NOT check LLM provider connectivity — that
    would make every health check slow and cost API credits every
    time a load balancer pings this endpoint.
    """
    db_status = "ok"
    try:
        db.execute(text("SELECT 1"))
    except Exception:  # noqa: BLE001
        db_status = "unreachable"

    return {
        "status": "ok",
        "app_name": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "database": db_status,
    }
