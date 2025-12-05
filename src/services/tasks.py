import asyncio
from datetime import datetime

from src.dependencies import container
from src.engines import producer
from src.enums import PriorityType, StatusType, ExchangeType, RoutingType, Priority
from src.repositories import TasksRepository
from src.schemes import (
    TaskCreateRequest,
    TaskCreateResponse,
    TasksRequest,
    TaskResponse,
    BaseQueryPathFilters,
    TaskId,
)


class TaskService:
    def __init__(self):
        self.tasks_repository: TasksRepository = container.resolve(TasksRepository)

    async def create_task(
        self,
        *,
        params: TaskCreateRequest,
    ) -> TaskCreateResponse:
        create_params = {**params.model_dump(), "status": StatusType.NEW}
        task = await self.tasks_repository.create(**create_params)

        await asyncio.sleep(10)

        task_id = task.id
        await producer.publish(
            exchange=ExchangeType.TASKS,
            routing_key=RoutingType.TASK,
            priority=Priority.get_priority_value(params.priority),
            body={"id": task_id, "priority": params.priority},
        )

        await self.tasks_repository.set_task_status(
            task_id=task_id, status=StatusType.PENDING
        )

        return TaskCreateResponse(**task.__dict__)

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
