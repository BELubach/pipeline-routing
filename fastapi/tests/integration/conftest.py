from typing import AsyncGenerator
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

from app.main import app
from app.db.session import get_db
from app.core.config import settings


# Create a test engine that doesn't pool connections
# This ensures each test gets a completely fresh connection
test_engine = create_async_engine(
    settings.DATABASE_URL,
    echo=True,
    poolclass=NullPool,  # Don't pool connections - create fresh ones for each test
)


@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Provide a database session for testing with automatic rollback.
    
    Each test gets a fresh connection and transaction that is rolled back
    after the test completes, ensuring test isolation.
    """
    # Create a fresh connection (not from a pool)
    connection = await test_engine.connect()
    
    # Start a transaction
    transaction = await connection.begin()
    
    # Create session bound to this connection and transaction  
    session = AsyncSession(
        bind=connection,
        expire_on_commit=False,
    )
    
    try:
        yield session
    finally:
        await session.close()
        # Rollback to undo all changes from this test
        await transaction.rollback()
        # Close connection (it won't be reused since we use NullPool)
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