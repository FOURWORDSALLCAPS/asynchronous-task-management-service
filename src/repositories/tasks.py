from src.engines import PostgresEngine
from src.models import TasksDB
from src.repositories import BaseRepository
from sqlalchemy import update, and_


class TasksRepository(BaseRepository):
    def __init__(self):
        db: PostgresEngine = PostgresEngine()
        super().__init__(db, TasksDB)

    async def set_task_status(self, task_id: int, status: str) -> None:
        stmt = update(TasksDB).where(and_(TasksDB.id == task_id)).values(status=status)
        await self.db.execute(stmt, no_return=True)  # noqa
