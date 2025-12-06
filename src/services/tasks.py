from http import HTTPStatus

from fastapi import HTTPException

from src.dependencies import container
from src.engines import producer
from src.enums import PriorityType, StatusType, ExchangeType, RoutingType, Priority
from src.repositories import TasksRepository
from src.schemes import (
    TaskCreateRequest,
    TaskCreateResponse,
    TaskResponse,
    TasksResponse,
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

    async def get_tasks(self, *, pagination: BaseQueryPathFilters) -> TasksResponse:
        tasks, pagination_info = await self.tasks_repository.get_tasks(
            pagination=pagination
        )

        data = [TaskResponse(**task.__dict__) for task in tasks]
        return TasksResponse(data=data, pagination=pagination_info)

    async def get_task(
        self,
        *,
        task_id: TaskId,
    ) -> TaskResponse:
        task = await self.tasks_repository.get_by(id=task_id)
        if not task:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail=f"Задача с номером {task_id} не найдена",
            )

        return TaskResponse(**task.__dict__)

    async def delete_task(
        self,
        *,
        task_id: TaskId,
    ) -> bool:
        task = await self.tasks_repository.get_by(id=task_id)
        if not task:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail=f"Задача с номером {task_id} не найдена",
            )

        await producer.publish(
            exchange=ExchangeType.TASKS,
            routing_key=RoutingType.TASK_CANCELED,
            priority=Priority.get_priority_value(PriorityType.HIGH),
            body={"id": task_id},
        )

        return True

    async def get_task_status(
        self,
        *,
        task_id: TaskId,
    ) -> StatusType:
        task = await self.tasks_repository.get_by(id=task_id)
        if not task:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail=f"Задача с номером {task_id} не найдена",
            )

        return StatusType(task.status)
