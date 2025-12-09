from datetime import datetime

import pytest
from unittest.mock import AsyncMock

from enums import StatusType, PriorityType, ExchangeType, RoutingType, Priority
from schemes import (
    TaskCreateRequest,
    TaskCreateResponse,
    BaseQueryPathFilters,
    TasksResponse,
    TaskResponse,
)
from schemes import Pagination


class TestTasksService:
    @pytest.mark.asyncio
    async def test_create_task(
        self, tasks_service, tasks_repository, producer, mock_task
    ):
        params = TaskCreateRequest(
            name="Test Task",
            description="Test Description",
            priority=PriorityType.HIGH,
        )

        tasks_repository.create.return_value = mock_task

        result = await tasks_service.create_task(params=params)

        tasks_repository.create.assert_called_once()

        create_kwargs = tasks_repository.create.call_args.kwargs
        assert create_kwargs["name"] == "Test Task"
        assert create_kwargs["description"] == "Test Description"
        assert create_kwargs["status"] == StatusType.NEW
        assert create_kwargs["priority"] == PriorityType.HIGH

        producer.publish.assert_called_once()

        publish_kwargs = producer.publish.call_args.kwargs
        assert publish_kwargs["exchange"] == ExchangeType.TASKS
        assert publish_kwargs["routing_key"] == RoutingType.TASK
        assert publish_kwargs["priority"] == Priority.get_priority_value(
            PriorityType.HIGH
        )
        assert publish_kwargs["body"] == {"id": 1, "priority": PriorityType.HIGH}

        assert isinstance(result, TaskCreateResponse)
        assert result.id == 1
        assert result.name == "Test Task"
        assert result.description == "Test Description"
        assert result.status == StatusType.NEW
        assert result.priority == PriorityType.MEDIUM
        assert result.created_at == datetime(2025, 1, 1, 10, 20, 0)

    @pytest.mark.asyncio
    async def test_get_tasks(self, tasks_service, tasks_repository, mock_task):
        pagination = BaseQueryPathFilters(
            page=1, page_size=25, count_only=False, pagination_on=True
        )

        mock_pagination_info = Pagination(
            total=10,
            page_count=1,
        )

        tasks_repository.get_tasks = AsyncMock(
            return_value=([mock_task], mock_pagination_info)
        )

        result = await tasks_service.get_tasks(pagination=pagination)

        tasks_repository.get_tasks.assert_called_once_with(pagination=pagination)

        assert isinstance(result, TasksResponse)
        assert hasattr(result, "data")
        assert hasattr(result, "pagination")

        assert len(result.data) == 1

        assert isinstance(result.data[0], TaskResponse)
        assert result.data[0].id == 1
        assert result.data[0].name == "Test Task"
        assert result.data[0].description == "Test Description"
        assert result.data[0].status == StatusType.NEW
        assert result.data[0].priority == PriorityType.MEDIUM
        assert result.data[0].created_at == datetime(2025, 1, 1, 10, 20, 0)
        assert result.data[0].stared_at == datetime(2025, 1, 1, 10, 30, 0)
        assert result.data[0].completed_at == datetime(2025, 1, 1, 10, 40, 0)
        assert result.data[0].result == "Result"
        assert result.data[0].error_info == ""

        assert result.pagination.total == 10
        assert result.pagination.page_count == 1

    @pytest.mark.asyncio
    async def test_get_task(self, tasks_service, tasks_repository, mock_task):
        tasks_repository.get_by = AsyncMock(return_value=mock_task)

        task_id = 1

        result = await tasks_service.get_task(task_id=task_id)

        assert isinstance(result, TaskResponse)
        assert result.id == 1
        assert result.name == "Test Task"
        assert result.description == "Test Description"
        assert result.status == StatusType.NEW
        assert result.priority == PriorityType.MEDIUM
        assert result.created_at == datetime(2025, 1, 1, 10, 20, 0)
        assert result.stared_at == datetime(2025, 1, 1, 10, 30, 0)
        assert result.completed_at == datetime(2025, 1, 1, 10, 40, 0)
        assert result.result == "Result"
        assert result.error_info == ""

    @pytest.mark.asyncio
    async def test_delete_task(
        self, tasks_service, tasks_repository, producer, mock_task
    ):
        tasks_repository.get_by.return_value = mock_task

        task_id = 1

        assert await tasks_service.delete_task(task_id=task_id)

        producer.publish.assert_called_once()

        publish_kwargs = producer.publish.call_args.kwargs
        assert publish_kwargs["exchange"] == ExchangeType.TASKS
        assert publish_kwargs["routing_key"] == RoutingType.TASK_CANCELED
        assert publish_kwargs["priority"] == Priority.get_priority_value(
            PriorityType.HIGH
        )
        assert publish_kwargs["body"] == {"id": 1}

    @pytest.mark.asyncio
    async def test_get_task_status(self, tasks_service, tasks_repository, mock_task):
        tasks_repository.get_by.return_value = mock_task

        task_id = 1

        result = await tasks_service.get_task_status(task_id=task_id)

        assert isinstance(result, StatusType)
        assert result == StatusType.NEW
