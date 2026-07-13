"""
Declarative base and shared mixins for all ORM models.

Every model in app/models/ inherits from `Base`, and most inherit
`UUIDPrimaryKeyMixin` and `TimestampMixin` too, so that the "every
table has a UUID primary key and created_at/updated_at columns" rule
from the Phase 1 database design is enforced in one place instead of
being repeated (and potentially getting out of sync) in every model
file.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import CHAR, TypeDecorator


class GUID(TypeDecorator):
    """
    Platform-independent UUID column.

    Postgres has a native UUID type; SQLite does not, so this stores
    UUIDs as 36-character strings there. Using this type instead of a
    raw String column means model code (`resume.id`) always works with
    real `uuid.UUID` objects regardless of which database is active,
    so switching from SQLite (dev) to Postgres (prod) requires no
    model changes.
    """

    impl = CHAR(36)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if isinstance(value, uuid.UUID):
            return str(value)
        return str(uuid.UUID(str(value)))

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        return uuid.UUID(str(value))


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""

    pass


class UUIDPrimaryKeyMixin:
    """Adds a UUID primary key column named `id`."""

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(), primary_key=True, default=uuid.uuid4
    )


class TimestampMixin:
    """Adds `created_at` and `updated_at` timestamp columns."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
