"""FastAPI dependency injection helpers."""

from collections.abc import Generator

from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.db.session import get_db


def get_settings_dependency() -> Settings:
    """Expose settings as a FastAPI dependency."""
    return get_settings()


def get_db_session() -> Generator[Session, None, None]:
    """Database session dependency alias."""
    yield from get_db()
