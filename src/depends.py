from dependencies import container
from engines import PostgresEngine
from repositories import TasksRepository


def init_container() -> None:
    container.add_instance(PostgresEngine())

    container.add_scoped(TasksRepository)
