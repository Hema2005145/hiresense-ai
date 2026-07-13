"""
Shared FastAPI dependency providers.

Route modules import from here instead of constructing services or
sessions inline. Centralizing this means:
- swapping an implementation (e.g. a different LLMProvider) happens
  in one place
- tests can override any of these with `app.dependency_overrides`
  without touching route code
"""

from __future__ import annotations

from collections.abc import Generator

from fastapi import Depends

from app.ai.llm_provider import LLMProvider, get_llm_provider
from app.config import Settings, get_settings
from app.db.session import get_db

__all__ = [
    "get_settings",
    "get_db",
    "get_llm_provider_dependency",
]


def get_llm_provider_dependency(
    settings: Settings = Depends(get_settings),
) -> Generator[LLMProvider, None, None]:
    """
    FastAPI dependency that yields a configured LLMProvider.

    Kept as a thin wrapper (rather than importing get_llm_provider
    directly in routes) so that future changes — e.g. caching a
    provider instance across requests instead of constructing it per
    request — only need to change here.
    """
    yield get_llm_provider(settings)


# Re-exported so routes can do:
#   from app.dependencies import get_db, get_settings
# and get a single, consistent import surface instead of reaching
# into app.db.session / app.config directly.
db_session_dependency = get_db
settings_dependency = get_settings
