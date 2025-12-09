import os
import sys
import pytest
from unittest.mock import AsyncMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from datetime import datetime
from types import SimpleNamespace

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from repositories import TasksRepository
from enums import StatusType, PriorityType
from engines import ProducerEngine
from services import TaskService


@pytest.fixture
def mock_db_session():
    session = AsyncMock(spec=AsyncSession)
    session.select = AsyncMock()
    session.select_one = AsyncMock()
    session.execute = AsyncMock()
    return session


@pytest.fixture
def tasks_repository(mock_db_session):
    repo = TasksRepository()
    repo.db = mock_db_session
    repo.create = AsyncMock()
    repo.get_by = AsyncMock()
    return repo


@pytest.fixture
def tasks_service(tasks_repository):
    with patch("dependencies.container.resolve", return_value=tasks_repository):
        service = TaskService()
        yield service


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


@pytest.fixture
def mock_task():
    task = SimpleNamespace()
    task.id = 1
    task.name = "Test Task"
    task.description = "Test Description"
    task.status = StatusType.NEW
    task.priority = PriorityType.MEDIUM
    task.created_at = datetime(2025, 1, 1, 10, 20, 0)
    task.stared_at = datetime(2025, 1, 1, 10, 30, 0)
    task.completed_at = datetime(2025, 1, 1, 10, 40, 0)
    task.result = "Result"
    task.error_info = ""
    return task
