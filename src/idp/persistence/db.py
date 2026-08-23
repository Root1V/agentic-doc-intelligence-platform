"""Async SQLAlchemy engine/session factory.

``get_session_factory`` is a plain (non-FastAPI-DI) cached accessor so both
the API layer (via ``api/deps.py``) and the background batch-processing task
(which outlives any single request's DI scope) share the same engine/pool
without duplicating engine-construction logic.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from idp.config import Settings

_engine_cache: dict[str, AsyncEngine] = {}
_factory_cache: dict[str, async_sessionmaker[AsyncSession]] = {}


def make_engine(settings: Settings) -> AsyncEngine:
    return create_async_engine(settings.database_url, pool_pre_ping=True)


def make_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False)


def get_session_factory(settings: Settings) -> async_sessionmaker[AsyncSession]:
    url = settings.database_url
    if url not in _factory_cache:
        engine = make_engine(settings)
        _engine_cache[url] = engine
        _factory_cache[url] = make_session_factory(engine)
    return _factory_cache[url]


def reset_engine_cache() -> None:
    """Drops the cached engine/session-factory without awaiting disposal.

    Only needed in tests: a real app process has exactly one event loop for
    its lifetime, so the cache is always valid. Tests can have several — in
    particular, FastAPI's ``TestClient`` bridges sync test code to the async
    app via its own dedicated thread+event loop (an anyio ``BlockingPortal``),
    distinct from pytest-asyncio's loop. Reusing an engine whose asyncpg
    connections were opened on one loop from a different loop raises
    'Future attached to a different loop'. Call this before constructing a
    ``TestClient`` in a test that also uses the DB outside of it.
    """
    _engine_cache.clear()
    _factory_cache.clear()
