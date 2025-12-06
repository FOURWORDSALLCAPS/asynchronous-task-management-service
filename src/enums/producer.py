from enum import StrEnum


class ExchangeType(StrEnum):
    TASKS = "tasks"


class RoutingType(StrEnum):
    TASK = "task"
    TASK_CANCELED = "task_canceled"
