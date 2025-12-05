from enum import StrEnum, IntEnum


class PriorityType(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class Priority(IntEnum):
    LOW = 1
    MEDIUM = 5
    HIGH = 10

    @staticmethod
    def get_priority_value(priority_type: PriorityType) -> int:
        mapping = {
            PriorityType.LOW: Priority.LOW,
            PriorityType.MEDIUM: Priority.MEDIUM,
            PriorityType.HIGH: Priority.HIGH,
        }
        return mapping[priority_type].value


class StatusType(StrEnum):
    NEW = "NEW"
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
