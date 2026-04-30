import asyncpg
from fastapi import Request

from .config import settings

_pool: asyncpg.Pool | None = None


async def create_pool() -> asyncpg.Pool:
    global _pool
    _pool = await asyncpg.create_pool(
        settings.database_url,
        min_size=settings.pool_min_size,
        max_size=settings.pool_max_size,
        command_timeout=10,
    )
    return _pool


async def close_pool():
    if _pool:
        await _pool.close()


def get_pool(request: Request) -> asyncpg.Pool:
    return request.app.state.pool
