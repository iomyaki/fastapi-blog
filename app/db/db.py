from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

sync_engine = create_engine(
    url=settings.db_url_psycopg,
    echo=True,
    pool_size=5,
    max_overflow=10,
)
async_engine = create_async_engine(
    url=settings.db_url_asyncpg,
    echo=True,
    pool_size=5,
    max_overflow=10,
)
sync_session = sessionmaker(sync_engine, autoflush=False, autocommit=False)
async_session = async_sessionmaker(async_engine, class_=AsyncSession)


def get_sync_db():
    with sync_session() as session:
        yield session


async def get_async_db():
    async with async_session() as session:
        yield session
