import asyncio
import logging
import sys
from contextlib import asynccontextmanager

from enums import ExchangeType
from services import TaskConsumer
from settings import settings

log = logging.getLogger(__name__)
stream_handler = logging.StreamHandler(sys.stderr)
stream_handler.setFormatter(logging.Formatter(settings.LOG_FORMAT))
log.addHandler(stream_handler)


class WorkerApplication:
    def __init__(self, task_consumer):
        self.task_consumer = task_consumer

    @asynccontextmanager
    async def lifespan(self):
        await self.startup()
        yield

        await self.task_consumer.stop()

    async def startup(self):
        await self.task_consumer.start()
        log.info("Воркеры успешно запущены")

    async def run(self):
        async with self.lifespan():
            await asyncio.sleep(1)


async def main():
    task_consumer = TaskConsumer(
        queue_name=ExchangeType.TASKS, max_workers=settings.WORKERS
    )
    app = WorkerApplication(task_consumer)
    await app.run()


if __name__ == "__main__":
    asyncio.run(main())
