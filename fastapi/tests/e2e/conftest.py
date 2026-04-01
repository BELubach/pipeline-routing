from typing import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.main import app
from app.db.session import engine, get_db


@pytest.fixture
async def test_engine():
    yield engine


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