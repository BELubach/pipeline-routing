import sys
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
import pytest
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
import asyncio
from app.main import app
from app.db.session import get_db


# =====================================================================
# WINDOWS ASYNC LOOP COMPATIBILITY PATCH FOR PSYCOPG
# =====================================================================
if sys.platform == "win32":
    # Tell asyncio to use the Selector event loop instead of Proactor
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


POSTGRES_ASYNC_URL = "postgresql+psycopg://postgres:postgres@localhost:5467/fastapi_db"
pg_async_engine = create_async_engine(POSTGRES_ASYNC_URL, pool_size=10, max_overflow=5)
PgAsyncSession = sessionmaker(pg_async_engine, class_=AsyncSession, expire_on_commit=False)

@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """
    E2E Client that forces FastAPI to use a thread-safe session factory pool.
    Every time a route asks for a database session, it gets a completely unique one.
    """
    # Force the dependency override to yield a completely separate session 
    # for each endpoint call, pulling directly from the connection pool.
    async def override_get_db():
        async with PgAsyncSession() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac
    
    # Clean up overrides after the test is done
    app.dependency_overrides.clear()
