import asyncio
import json
import logging
import sys
from collections.abc import Awaitable
from typing import Optional, Callable

import aio_pika
from aio_pika.abc import (
    AbstractChannel,
    AbstractRobustConnection,
    AbstractIncomingMessage,
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
        return await aio_pika.connect_robust(self.amqp_url)

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


class ProducerEngine:
    def __init__(self) -> None:
        self.connector = rabbit_manager

    async def publish(self, exchange: str, routing_key: str, body: dict) -> None:
        body_bytes = json.dumps(body).encode("utf-8")

        async with self.connector.channel_pool.acquire() as channel:
            exchange_obj = await channel.get_exchange(exchange, ensure=True)
            await exchange_obj.publish(
                aio_pika.Message(body=body_bytes), routing_key=routing_key
            )


producer = ProducerEngine()


class ConsumerEngine:
    def __init__(self) -> None:
        self.connector = rabbit_manager
        self.callback: Optional[Callable[[dict], Awaitable[None]]] = None
        self.__consume_tasks: list[asyncio.Task] = []
        self._is_consuming = False

    def set_callback(self, callback: Callable[[dict], Awaitable[None]]) -> None:
        self.callback = callback

    async def _message_handler(self, message: AbstractIncomingMessage) -> None:
        async with message.process():
            try:
                body = json.loads(message.body.decode())
                await self.callback(body)
            except json.JSONDecodeError as e:
                log.error(
                    f"Ошибка декодирования JSON: {e}, body: {message.body.decode()}"
                )
            except Exception as e:
                log.error(f"Ошибка обработки сообщения: {e}")

    async def consume(
        self, queue_name: str, durable: bool = True, prefetch_count: int = 1
    ) -> None:
        self._is_consuming = True

        async with self.connector.channel_pool.acquire() as channel:
            await channel.set_qos(prefetch_count=prefetch_count)
            queue = await channel.declare_queue(
                queue_name, durable=durable, auto_delete=not durable
            )

            await queue.consume(self._message_handler)

            log.info(f"Ожидание сообщений в очереди '{queue_name}'...")
            print("queue_name", queue_name)
            while self._is_consuming:
                await asyncio.sleep(1)

    async def consume_multiple(
        self, queues: list[str], durable: bool = True, prefetch_count: int = 1
    ) -> list[asyncio.Task]:
        tasks = []
        for queue_name in queues:
            task = asyncio.create_task(
                self.consume(queue_name, durable, prefetch_count),
                name=f"consume-{queue_name}",
            )
            tasks.append(task)
        self.__consume_tasks = tasks
        return tasks

    async def stop_consuming(self) -> None:
        self._is_consuming = False

        if consume_tasks := self.__consume_tasks:
            for task in consume_tasks:
                task.cancel()
            await asyncio.gather(*self.__consume_tasks, return_exceptions=True)

            self.__consume_tasks.clear()


consumer = ConsumerEngine()
