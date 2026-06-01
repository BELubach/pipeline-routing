"""
Configuration for pytest - defines fixtures for testing the FastAPI application

All unit tests run with the default SQLite in-memory database using aiosqlite to make tests run with the async processor. 
This allows for fast test execution without needing a Docker container.
"""

from typing import AsyncGenerator
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from app.main import app
from app.db.session import get_db, sqlite_engine


@pytest.fixture
async def test_engine():
    from app.models.user import User

    async with sqlite_engine.begin() as conn:
        await conn.run_sync(User.__table__.drop, checkfirst=True)
        await conn.run_sync(User.__table__.create, checkfirst=True)

    yield sqlite_engine


@pytest.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    connection = await test_engine.connect()
    transaction = await connection.begin()

    session = async_sessionmaker(
        bind=connection,
        class_=AsyncSession,
        expire_on_commit=False,
        join_transaction_mode="create_savepoint",
    )()

    yield session

    await session.close()
    await transaction.rollback()
    await connection.close()


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()