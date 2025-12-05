from datetime import datetime

from engines import PostgresEngine
from models import TasksDB
from repositories import BaseRepository
from sqlalchemy import update, and_


class TasksRepository(BaseRepository):
    def __init__(self):
        db: PostgresEngine = PostgresEngine()
        super().__init__(db, TasksDB)

    async def set_task_status(self, task_id: int, status: str) -> None:
        stmt = update(TasksDB).where(and_(TasksDB.id == task_id)).values(status=status)
        await self.db.execute(stmt, no_return=True)  # noqa

    async def set_task_stared_at(self, task_id: int, stared_at: datetime) -> None:
        stmt = (
            update(TasksDB)
            .where(and_(TasksDB.id == task_id))
            .values(stared_at=stared_at)
        )
        await self.db.execute(stmt, no_return=True)  # noqa

    async def set_task_completed_at(self, task_id: int, completed_at: datetime) -> None:
        stmt = (
            update(TasksDB)
            .where(and_(TasksDB.id == task_id))
            .values(completed_at=completed_at)
        )
        await self.db.execute(stmt, no_return=True)  # noqa

    async def set_task_result(self, task_id: int, result: str) -> None:
        if not result:
            return

        stmt = update(TasksDB).where(and_(TasksDB.id == task_id)).values(result=result)
        await self.db.execute(stmt, no_return=True)  # noqa

    async def set_task_error_info(self, task_id: int, error_info: str) -> None:
        if not error_info:
            return

        stmt = (
            update(TasksDB)
            .where(and_(TasksDB.id == task_id))
            .values(error_info=error_info)
        )
        await self.db.execute(stmt, no_return=True)  # noqa
