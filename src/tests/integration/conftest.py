from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.engine import ChunkedIteratorResult

from models import Base
from repositories import TasksRepository
from engines import ProducerEngine
from settings import settings
from main import app


class CustomAsyncSession(AsyncSession):
    async def execute(
        self, stmt, execution_options=None, no_return=False, return_many=False, **kwargs
    ):
        cursor = await super().execute(
            stmt, execution_options=execution_options, **kwargs
        )

        await self.commit()

        if no_return:
            return None
        if return_many:
            return cursor.scalars().all()
        return cursor.scalar_one_or_none()


async def make_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(
        engine,
        class_=CustomAsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )


@asynccontextmanager
async def runtime_engine() -> AsyncIterator[AsyncEngine]:
    engine = create_async_engine(
        url=settings.get_test_postgres_uri_asyncpg,
        echo=True,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
        pool_recycle=3600,
    )
    try:
        yield engine
    finally:
        await engine.dispose()


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with runtime_engine() as engine:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)

        session_factory = await make_session_factory(engine)

        async with session_factory() as session:
            with patch("dependencies.container.resolve") as mock_resolve:
                repository = TasksRepository()
                repository.db = session
                mock_resolve.return_value = repository

                try:
                    yield session
                finally:
                    await session.close()


@pytest.fixture
async def async_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test", timeout=30.0
    ) as client:
        yield client


@pytest.fixture
def mock_chunked_iterator_result():
    mock_task = MagicMock()
    mock_task.id = 1
    mock_task.name = "Test Task"
    mock_task.description = "Test Description"
    mock_task.status = "NEW"
    mock_task.priority = "HIGH"
    mock_task.__dict__ = {
        "id": 1,
        "name": "Test Task",
        "description": "Test Description",
        "status": "NEW",
        "priority": "HIGH",
    }

    original_getattr = ChunkedIteratorResult.__getattribute__

    def mock_getattr(self, name):
        if name in ["id", "name", "description", "status", "priority"]:
            return getattr(mock_task, name)
        if name == "scalar_one":
            return lambda: mock_task
        return original_getattr(self, name)

    with patch.object(ChunkedIteratorResult, "__getattribute__", mock_getattr):
        yield


@pytest.fixture
def mock_rabbit_manager():
    manager = AsyncMock()
    manager.channel_pool = AsyncMock()
    mock_channel = AsyncMock()
    manager.channel_pool.acquire.return_value.__aenter__.return_value = mock_channel
    return manager


@pytest.fixture
def producer_engine(mock_rabbit_manager):
    engine = ProducerEngine()
    engine.connector = mock_rabbit_manager
    engine.publish = AsyncMock()
    return engine


@pytest.fixture
def producer(producer_engine):
    with patch("services.tasks.producer", producer_engine):
        yield producer_engine
