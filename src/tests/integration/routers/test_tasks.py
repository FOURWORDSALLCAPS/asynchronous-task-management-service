import pytest

from enums import StatusType, PriorityType
from models import TasksDB


@pytest.mark.integration
@pytest.mark.asyncio
class TestTasksAPI:
    async def test_create_task(
        self, producer, mock_chunked_iterator_result, async_client, db_session
    ):
        task_json = {
            "name": "Test API Task",
            "description": "Created API endpoint",
            "priority": PriorityType.HIGH,
        }

        response = await async_client.post("/api/v1/tasks/", json=task_json)

        assert response.status_code == 200

        response = response.json()

        assert "id" in response
        assert response["name"] == task_json["name"]
        assert response["description"] == task_json["description"]
        assert response["priority"] == task_json["priority"]
        assert response["status"] == StatusType.PENDING

        task_id = response["id"]
        db_task = await db_session.get(TasksDB, task_id)

        assert db_task is not None
        assert db_task.name == task_json["name"]
        assert db_task.description == task_json["description"]
        assert db_task.priority.value == task_json["priority"]
        assert db_task.status == StatusType.PENDING
