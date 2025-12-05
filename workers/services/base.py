from abc import ABC, abstractmethod

import aio_pika

from enums import PriorityType
from engines import consumer


class BaseWorker(ABC):
    def __init__(self, queue_name: str, prefetch_count: int = 10):
        self.queue_name = queue_name
        self.prefetch_count = prefetch_count

    async def start(self):
        consumer.set_callback(self.process_message)

        queues = [PriorityType.HIGH, PriorityType.MEDIUM, PriorityType.LOW]
        await consumer.consume_multiple(queues)

    @abstractmethod
    async def process_message(self, message: aio_pika.IncomingMessage):
        pass
