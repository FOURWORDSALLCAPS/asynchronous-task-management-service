import asyncio
import logging
import signal
import sys
from contextlib import asynccontextmanager

from engines import consumer
from enums import RoutingType, ExchangeType
from services import TaskConsumer
from settings import settings

log = logging.getLogger(__name__)
stream_handler = logging.StreamHandler(sys.stderr)
stream_handler.setFormatter(logging.Formatter(settings.LOG_FORMAT))
log.addHandler(stream_handler)


class WorkerApplication:
    def __init__(self, task_consumer):
        self.task_consumer = task_consumer
        self.shutdown_event = asyncio.Event()

    @asynccontextmanager
    async def lifespan(self):
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, self.shutdown_event.set)

        try:
            await consumer.setup_queue(
                queue_name=RoutingType.TASK,
                exchange_name=ExchangeType.TASKS,
                max_priority=3,
            )
            await consumer.setup_queue(
                queue_name=RoutingType.TASK_CANCELED, exchange_name=ExchangeType.TASKS
            )

            consumer.set_callback(
                queue_name=RoutingType.TASK, callback=self.task_consumer.process_message
            )
            consumer.set_callback(
                queue_name=RoutingType.TASK_CANCELED,
                callback=self.task_consumer.cancel_task,
            )

            queues = [RoutingType.TASK, RoutingType.TASK_CANCELED]
            await consumer.consume_multiple(queues)

            yield
        finally:
            await self.task_consumer.stop()
            await consumer.stop_consuming()

    async def run(self):
        async with self.lifespan():
            await self.shutdown_event.wait()


async def main():
    task_consumer = TaskConsumer(
        queue_name=ExchangeType.TASKS, max_workers=settings.WORKERS
    )
    app = WorkerApplication(task_consumer)
    await app.run()


if __name__ == "__main__":
    asyncio.run(main())
