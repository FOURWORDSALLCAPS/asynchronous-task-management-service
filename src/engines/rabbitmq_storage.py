import json
from typing import Optional

from aio_pika import connect_robust, Message
from aio_pika.abc import AbstractChannel, AbstractRobustConnection
from aio_pika.pool import Pool

from settings import settings


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


class ProducerEngine:
    def __init__(self) -> None:
        self.connector = rabbit_manager

    async def publish(
        self, exchange: str, routing_key: str, priority: int, body: dict
    ) -> None:
        body_bytes = json.dumps(body).encode("utf-8")

        async with self.connector.channel_pool.acquire() as channel:
            exchange_obj = await channel.get_exchange(exchange, ensure=True)
            await exchange_obj.publish(
                Message(body=body_bytes, priority=priority), routing_key=routing_key
            )


producer = ProducerEngine()
