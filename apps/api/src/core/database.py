import logging
from collections.abc import AsyncGenerator

from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.core.config import get_settings

_async_engine: AsyncEngine | None = None
_async_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_async_engine() -> AsyncEngine:
    global _async_engine

    if _async_engine is None:
        settings = get_settings()
        _async_engine = create_async_engine(
            settings.database.async_url,
            pool_size=settings.database.pool_size,
            max_overflow=settings.database.max_overflow,
            pool_pre_ping=True,
            pool_recycle=3600,
            echo=settings.db_echo_log,
        )
        logging.info("Async engine created successfully")

    return _async_engine


def get_async_session_factory() -> async_sessionmaker[AsyncSession]:
    global _async_session_factory

    if _async_session_factory is None:
        _async_session_factory = async_sessionmaker(
            bind=get_async_engine(),
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
        )

    return _async_session_factory


async def dispose_database() -> None:
    global _async_engine, _async_session_factory
    if _async_engine is not None:
        logging.info("Disposing database engine...")
        await _async_engine.dispose()
        _async_engine = None
        _async_session_factory = None
        logging.info("Database engine disposed")


async def get_async_db_session() -> AsyncGenerator[AsyncSession, None]:
    session_factory = get_async_session_factory()
    async with session_factory() as session:
        try:
            yield session
        except HTTPException:
            await session.rollback()
            raise
        except Exception as exc:
            logging.exception("Session rollback due to exception: %s", exc)
            await session.rollback()
            raise


async def check_database_connection() -> bool:
    try:
        engine = get_async_engine()
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
        logging.debug("Database connection check: OK")
        return True
    except Exception:
        logging.exception("Database connection check failed")
        return False
