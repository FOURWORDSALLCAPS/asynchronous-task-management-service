from datetime import datetime

from pydantic import BaseModel, Field, field_serializer

from src.enums import PriorityType, StatusType


class TaskCreate(BaseModel):
    name: str = Field(
        description="Название",
        examples=["Задача"],
    )
    description: str = Field(
        default="",
        description="Описание",
        examples=["Подготовка пробирок"],
    )
    priority: PriorityType = Field(
        description="Приоритет",
        examples=[PriorityType.LOW],
    )


class TaskCreateRequest(TaskCreate): ...


class TaskResponse(TaskCreate):
    id: int = Field(
        description="Уникальный идентификатор",
        examples=["129"],
    )
    status: StatusType = Field(
        description="Статус",
        examples=[StatusType.NEW],
    )
    created_at: datetime = Field(
        description="Время создания",
        examples=["2025-12-04 12:10:00"],
    )
    stared_at: datetime | None = Field(
        default=None,
        description="Время начала",
        examples=["2025-12-04 12:20:00"],
    )
    completed_at: datetime | None = Field(
        default=None,
        description="Время завершения",
        examples=["2025-12-04 12:30:00"],
    )
    result: str | None = Field(
        default="",
        description="Результат выполнения",
        examples=["Пробирка 314123 готова"],
    )
    error_info: str | None = Field(
        default="",
        description="Информация об ошибках",
        examples=["Сбой проверки кода пробирки"],
    )

    @field_serializer("created_at", "stared_at", "completed_at")
    def serialize_date_time_to_str(field: datetime):
        if field:
            return field.strftime("%Y-%m-%d %H:%M:%S")


class TaskCreateResponse(TaskResponse): ...


class TasksRequest(BaseModel):
    priority: PriorityType = Field(
        description="Приоритет",
        examples=[PriorityType.HIGH],
    )
    status: StatusType = Field(
        description="Статус",
        examples=[StatusType.FAILED],
    )
