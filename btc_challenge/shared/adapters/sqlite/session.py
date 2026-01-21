from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from functools import lru_cache

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from btc_challenge.config import AppConfig


@lru_cache(1)
def get_async_engine(echo: bool = False) -> AsyncEngine:
    return create_async_engine(url=AppConfig.sqlite.async_url, echo=echo)


@lru_cache(1)
def get_async_sessionmaker(
    engine: AsyncEngine = get_async_engine(),
) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(bind=engine, expire_on_commit=False)


@asynccontextmanager
async def get_async_session(
    session_factory: async_sessionmaker[AsyncSession] = get_async_sessionmaker(),
) -> AsyncGenerator[AsyncSession]:
    async with session_factory() as session:
        try:
            yield session
        finally:
            await session.close()
