from datetime import datetime

from src.enums import PriorityType, StatusType
from src.schemes import (
    TaskCreateRequest,
    TaskCreateResponse,
    TasksRequest,
    TaskResponse,
    BaseQueryPathFilters,
    TaskId,
)


class TaskService:
    def __init__(self): ...

    async def create_task(
        self,
        *,
        params: TaskCreateRequest,
    ) -> TaskCreateResponse:
        return TaskCreateResponse(
            id=1,
            name="Задача",
            description="",
            priority=PriorityType.LOW,
            status=StatusType.NEW,
            created_at=datetime.now(),
            stared_at=None,
            completed_at=None,
            result="",
            error_info="",
        )

    async def get_tasks(
        self, *, params: TasksRequest, pagination: BaseQueryPathFilters
    ) -> list[TaskResponse]:
        result = [
            TaskResponse(
                id=1,
                name="Задача",
                description="",
                priority=params.priority,
                status=params.status,
                created_at=datetime.now(),
                stared_at=None,
                completed_at=None,
                result="",
                error_info="",
            )
        ]
        return result

    async def get_task(
        self,
        *,
        task_id: TaskId,
    ) -> TaskResponse:
        return TaskResponse(
            id=1,
            name="Задача",
            description="",
            priority=PriorityType.MEDIUM,
            status=StatusType.PENDING,
            created_at=datetime.now(),
            stared_at=None,
            completed_at=None,
            result="",
            error_info="",
        )

    async def delete_task(
        self,
        *,
        task_id: TaskId,
    ) -> bool:
        return True

    async def get_task_status(
        self,
        *,
        task_id: TaskId,
    ) -> StatusType:
        return StatusType.PENDING
