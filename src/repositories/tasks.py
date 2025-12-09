from pydantic import BaseModel
from sqlalchemy import select, update, and_, func

from engines import PostgresEngine
from models import TasksDB
from repositories import BaseRepository
from schemes.base import Pagination


class TasksRepository(BaseRepository):
    def __init__(self):
        db: PostgresEngine = PostgresEngine()
        super().__init__(db, TasksDB)

    async def set_task_status(self, task_id: int, status: str) -> None:
        stmt = update(TasksDB).where(and_(TasksDB.id == task_id)).values(status=status)
        await self.db.execute(stmt, no_return=True)  # noqa

    async def get_tasks(
        self, pagination: BaseModel
    ) -> tuple[list[TasksDB], Pagination]:
        stmt = select(TasksDB)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        result = await self.db.execute(count_stmt, return_many=True)  # noqa
        total_records = result[0] or 0

        if not pagination.pagination_on or pagination.page_size <= 0:
            page_count = 0
        else:
            page_count = (
                total_records + pagination.page_size - 1
            ) // pagination.page_size

        if pagination.count_only:
            return [], Pagination(total=total_records, page_count=page_count)

        stmt = stmt.order_by(TasksDB.created_at.desc())

        if pagination.pagination_on:
            offset = (pagination.page - 1) * pagination.page_size
            stmt = stmt.offset(offset).limit(pagination.page_size)

        result = await self.db.execute(stmt, return_many=True)  # noqa

        pagination_info = Pagination(total=total_records, page_count=page_count)

        return result or [], pagination_info
