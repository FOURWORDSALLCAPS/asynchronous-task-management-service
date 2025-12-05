from abc import ABC, abstractmethod

import aio_pika


class BaseWorker(ABC):
    def __init__(self, queue_name: str, prefetch_count: int = 10):
        self.queue_name = queue_name
        self.prefetch_count = prefetch_count

    @abstractmethod
    async def process_message(self, message: aio_pika.IncomingMessage):
        pass
