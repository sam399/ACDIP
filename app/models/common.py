"""Shared model helpers that do not alter the existing database schema."""

from datetime import UTC, datetime


def utc_now() -> datetime:
    """Return naive UTC for compatibility with the existing SQLite columns."""
    return datetime.now(UTC).replace(tzinfo=None)
