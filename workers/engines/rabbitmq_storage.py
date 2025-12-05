import asyncio
import json
import logging
import sys
from collections.abc import Awaitable
from typing import Optional, Callable

from aio_pika import connect_robust
from aio_pika.abc import (
    AbstractChannel,
    AbstractRobustConnection,
    AbstractIncomingMessage,
    ExchangeType as pika_exchange_type,
)
from aio_pika.pool import Pool

from settings import settings

log = logging.getLogger(__name__)
stream_handler = logging.StreamHandler(sys.stderr)
stream_handler.setFormatter(logging.Formatter(settings.LOG_FORMAT))
log.addHandler(stream_handler)


class RabbitMQEngine:
    def __init__(self, amqp_url: str) -> None:
        self.amqp_url = amqp_url
        self._connection_pool: Optional[Pool] = None
        self._channel_pool: Optional[Pool] = None

    async def get_connection(self) -> AbstractRobustConnection:
        return await connect_robust(self.amqp_url)

    async def get_channel(self) -> AbstractChannel:
        async with self.connection_pool.acquire() as connection:
            return await connection.channel()

    @property
    def connection_pool(self) -> Pool:
        if self._connection_pool is None:
            self._connection_pool = Pool(self.get_connection, max_size=10)
        return self._connection_pool

    @property
    def channel_pool(self) -> Pool:
        if self._channel_pool is None:
            self._channel_pool = Pool(self.get_channel, max_size=20)
        return self._channel_pool

    async def close(self) -> None:
        if self._channel_pool:
            await self._channel_pool.close()
        if self._connection_pool:
            await self._connection_pool.close()


rabbit_manager = RabbitMQEngine(settings.get_rabbitmq_uri)


class ConsumerEngine:
    def __init__(self) -> None:
        self.connector = rabbit_manager
        self.queue_callbacks: dict[str, Callable[[dict], Awaitable[None]]] = {}
        self.consume_tasks: list[asyncio.Task] = []
        self.is_consuming = False

    def set_callback(
        self, queue_name: str, callback: Callable[[dict], Awaitable[None]]
    ) -> None:
        self.queue_callbacks[queue_name] = callback

    async def _message_handler(self, message: AbstractIncomingMessage) -> None:
        async with message.process():
            try:
                body = json.loads(message.body.decode())
                queue_name = message.routing_key
                callback = self.queue_callbacks.get(queue_name)
                await callback(body)
            except json.JSONDecodeError as e:
                log.error(
                    f"Ошибка декодирования JSON: {e}, body: {message.body.decode()}"
                )
            except Exception as e:
                log.error(f"Ошибка обработки сообщения: {e}")

    async def setup_queue(
        self,
        queue_name: str,
        exchange_name: str,
        durable: bool = True,
        max_priority: int = None,
    ) -> None:
        async with self.connector.channel_pool.acquire() as channel:
            exchange = await channel.declare_exchange(
                exchange_name, pika_exchange_type.TOPIC, durable=durable
            )

            queue = await channel.declare_queue(
                queue_name,
                durable=durable,
                auto_delete=not durable,
                arguments={"x-max-priority": max_priority} if max_priority else None,
            )

            await queue.bind(exchange, queue_name)

    async def consume(self, queue_name: str, prefetch_count: int = 1) -> None:
        self.is_consuming = True

        async with self.connector.channel_pool.acquire() as channel:
            await channel.set_qos(prefetch_count=prefetch_count)

            queue = await channel.get_queue(queue_name)

            await queue.consume(self._message_handler)

            log.info(f"Ожидание сообщений в очереди '{queue_name}'...")
            while self.is_consuming:
                await asyncio.sleep(1)

    async def consume_multiple(
        self, queues: list[str], prefetch_count: int = 1
    ) -> list[asyncio.Task]:
        tasks = []
        for queue_name in queues:
            task = asyncio.create_task(
                self.consume(queue_name, prefetch_count),
                name=f"consume-{queue_name}",
            )
            tasks.append(task)
        self.consume_tasks = tasks
        return tasks

    async def stop_consuming(self) -> None:
        self.is_consuming = False

        if consume_tasks := self.consume_tasks:
            for task in consume_tasks:
                task.cancel()
            await asyncio.gather(*self.consume_tasks, return_exceptions=True)

            self.consume_tasks.clear()


consumer = ConsumerEngine()
