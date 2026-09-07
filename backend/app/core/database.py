from collections.abc import AsyncIterator
from typing import Any

from sqlalchemy import MetaData, event
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

NAMING_CONVENTION: dict[str, str] = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


def _engine_kwargs(database_url: str) -> dict[str, Any]:
    if database_url.startswith("sqlite"):
        return {}
    return {"pool_size": 5, "max_overflow": 10}


def _unicode_lower(value: Any) -> Any:
    return value.lower() if isinstance(value, str) else value


def _enable_sqlite_foreign_keys(engine: AsyncEngine, database_url: str) -> None:
    if not database_url.startswith("sqlite"):
        return

    @event.listens_for(engine.sync_engine, "connect")
    def _configure_sqlite(dbapi_connection: Any, _record: Any) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
        # Override SQLite's ASCII-only lower() with a Unicode-aware version so
        # case-insensitive LIKE works for non-ASCII (e.g. Cyrillic) search.
        dbapi_connection.create_function("lower", 1, _unicode_lower)


def create_engine(database_url: str | None = None) -> AsyncEngine:
    url = database_url or settings.database_url
    engine = create_async_engine(url, echo=False, **_engine_kwargs(url))
    _enable_sqlite_foreign_keys(engine, url)
    return engine


engine = create_engine()

session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_session() -> AsyncIterator[AsyncSession]:
    async with session_factory() as session:
        yield session
