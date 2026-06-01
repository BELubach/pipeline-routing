from typing import AsyncGenerator

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings


SQLITE_TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


def _build_sync_database_url(database_url: str) -> str:
    if database_url.startswith("postgresql+asyncpg://"):
        return database_url.replace("postgresql+asyncpg://", "postgresql+psycopg://", 1)
    if database_url.startswith("sqlite+aiosqlite://"):
        return database_url.replace("sqlite+aiosqlite://", "sqlite://", 1)
    return database_url

# Main Docker/Postgres database used by the application and e2e tests.
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=True,
    future=True,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

sync_db_url = _build_sync_database_url(settings.DATABASE_URL)
sync_engine = create_engine(
    sync_db_url,
    echo=False,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=sync_engine,
)

# SQLite database used by endpoint-level integration tests.
sqlite_engine = create_async_engine(
    SQLITE_TEST_DATABASE_URL,
    echo=False,
    future=True,
    poolclass=StaticPool,
    connect_args={"check_same_thread": False},
)

SQLiteAsyncSessionLocal = async_sessionmaker(
    sqlite_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

sqlite_sync_engine = create_engine(
    _build_sync_database_url(SQLITE_TEST_DATABASE_URL),
    echo=False,
    poolclass=StaticPool,
    connect_args={"check_same_thread": False},
)

SQLiteSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=sqlite_sync_engine,
)

# Base class for models
Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting async database sessions"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_sqlite_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting async SQLite sessions in integration tests"""
    async with SQLiteAsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
