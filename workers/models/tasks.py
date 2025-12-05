from datetime import datetime
from sqlalchemy import func, Enum, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from enums import PriorityType, StatusType
from models.base import Base


class TasksDB(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
        comment="Уникальный идентификатор",
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Название",
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=True,
        comment="Описание",
    )
    priority: Mapped[PriorityType] = mapped_column(
        Enum(PriorityType),
        nullable=False,
        comment="Приоритет",
    )
    status: Mapped[StatusType] = mapped_column(
        Enum(StatusType),
        nullable=False,
        comment="Статус",
    )
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        nullable=False,
        comment="Время создания",
    )
    stared_at: Mapped[datetime] = mapped_column(
        nullable=True,
        comment="Время начала",
    )
    completed_at: Mapped[datetime] = mapped_column(
        nullable=True,
        comment="Время завершения",
    )
    result: Mapped[str] = mapped_column(
        nullable=True,
        comment="Результат выполнения",
    )
    error_info: Mapped[str] = mapped_column(
        Text,
        nullable=True,
        comment="Информация об ошибках",
    )
