from src.dependencies import container
from src.engines import PostgresEngine
from src.repositories import TasksRepository


def init_container() -> None:
    container.add_instance(PostgresEngine())

    container.add_scoped(TasksRepository)
