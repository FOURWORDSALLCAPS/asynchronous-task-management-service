from fastapi import APIRouter, Depends

from src.enums import StatusType
from src.schemes import (
    TaskCreateRequest,
    TaskCreateResponse,
    TaskResponse,
    BaseQueryPathFilters,
    TasksRequest,
    TaskId,
)
from src.services import TaskService

router = APIRouter(
    prefix="/tasks",
    tags=["Tasks"],
)


@router.post("/", response_model=TaskCreateResponse)
async def create_task(
    params: TaskCreateRequest,
    task_service: TaskService = Depends(),
) -> TaskCreateResponse:
    return await task_service.create_task(params=params)


@router.get("/", response_model=list[TaskResponse])
async def get_tasks(
    params: TasksRequest = Depends(),
    pagination: BaseQueryPathFilters = Depends(),
    task_service: TaskService = Depends(),
) -> list[TaskResponse]:
    return await task_service.get_tasks(params=params, pagination=pagination)


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: TaskId,
    task_service: TaskService = Depends(),
) -> TaskResponse:
    return await task_service.get_task(task_id=task_id)


@router.delete("/{task_id}", response_model=bool)
async def delete_task(
    task_id: TaskId,
    task_service: TaskService = Depends(),
) -> bool:
    return await task_service.delete_task(task_id=task_id)


@router.get("/{task_id}/status", response_model=StatusType)
async def get_task_status(
    task_id: TaskId,
    task_service: TaskService = Depends(),
) -> StatusType:
    return await task_service.get_task_status(task_id=task_id)
