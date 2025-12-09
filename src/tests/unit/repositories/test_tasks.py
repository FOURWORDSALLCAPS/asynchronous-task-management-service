import pytest
from sqlalchemy.sql.dml import Update
from unittest.mock import MagicMock

from enums import StatusType
from models import TasksDB
from schemes import BaseQueryPathFilters


class TestTasksRepository:
    @pytest.mark.asyncio
    async def test_set_task_status(self, tasks_repository, mock_db_session):
        task_id = 1
        status = StatusType.NEW

        await tasks_repository.set_task_status(task_id, status)
        mock_db_session.execute.assert_called_once()
        call_args = mock_db_session.execute.call_args[0][0]

        assert isinstance(call_args, Update)

    @pytest.mark.asyncio
    async def test_get_tasks(self, tasks_repository, mock_db_session):
        pagination = BaseQueryPathFilters(
            page=1, page_size=25, count_only=False, pagination_on=True
        )

        mock_task1 = MagicMock(spec=TasksDB)
        mock_task1.id = 1
        mock_task1.name = "Task 1"
        mock_task1.status = StatusType.NEW

        mock_task2 = MagicMock(spec=TasksDB)
        mock_task2.id = 2
        mock_task2.name = "Task 2"
        mock_task2.status = StatusType.IN_PROGRESS

        mock_db_session.execute.side_effect = [[10], [mock_task1, mock_task2]]

        tasks, pagination_info = await tasks_repository.get_tasks(pagination)
        assert mock_db_session.execute.call_count == 2

        assert len(tasks) == 2
        assert tasks[0].id == 1
        assert tasks[1].id == 2

        assert pagination_info.total == 10
        assert pagination_info.page_count == 1
