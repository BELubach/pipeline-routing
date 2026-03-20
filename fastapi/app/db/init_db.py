from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import engine
from app.db.base import Base


async def init_db() -> None:
    """Initialize database - create all tables"""
    async with engine.begin() as conn:
        # Enable PostGIS extension
        await conn.execute("CREATE EXTENSION IF NOT EXISTS postgis")
        
        # Create all tables
        await Base.metadata.create_all(conn)
