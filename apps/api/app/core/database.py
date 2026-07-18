from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from typing import AsyncGenerator
from app.core.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_timeout=settings.DB_POOL_TIMEOUT_SECONDS,
    pool_recycle=settings.DB_POOL_RECYCLE_SECONDS,
    connect_args={"timeout": settings.DB_CONNECT_TIMEOUT_SECONDS},
    echo=False,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
