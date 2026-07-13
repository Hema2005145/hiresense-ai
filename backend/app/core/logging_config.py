"""
Logging configuration.

Configures a single root logger setup used across the whole app.
Every module should call `logging.getLogger(__name__)` and rely on
this configuration rather than calling `print()` — print statements
are invisible in production log aggregators (Render/Railway capture
stdout, but without levels, timestamps, or module names, debugging a
production incident becomes guesswork).
"""

from __future__ import annotations

import logging
import sys

from app.config import get_settings

_LOG_FORMAT = (
    "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
)
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def configure_logging() -> None:
    """
    Configures the root logger.

    Called once, at application startup, from main.py's lifespan
    function. Idempotent: calling it more than once will not create
    duplicate handlers.
    """
    settings = get_settings()
    root_logger = logging.getLogger()

    # Avoid attaching duplicate handlers if configure_logging() is
    # called more than once (e.g. in tests that re-import main).
    if root_logger.handlers:
        return

    root_logger.setLevel(settings.log_level)

    handler = logging.StreamHandler(stream=sys.stdout)
    handler.setFormatter(logging.Formatter(fmt=_LOG_FORMAT, datefmt=_DATE_FORMAT))
    root_logger.addHandler(handler)

    # Quiet down noisy third-party loggers so app logs aren't drowned out.
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if settings.debug else logging.WARNING
    )
