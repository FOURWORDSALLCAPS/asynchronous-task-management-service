import logging
import sys
from typing import Any

from sqlalchemy.exc import (
    IntegrityError,
    InterfaceError,
    OperationalError,
    ProgrammingError,
)
from sqlalchemy.ext.asyncio import (
    AsyncResult,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from models.base import Base
from settings import settings

log = logging.getLogger(__name__)
stream_handler = logging.StreamHandler(sys.stderr)
stream_handler.setFormatter(logging.Formatter(settings.LOG_FORMAT))
log.addHandler(stream_handler)


class PostgresEngine:
    def __init__(self) -> None:
        self.engine = create_async_engine(
            url=settings.get_postgres_uri_asyncpg,
            echo=False,
            echo_pool=False,
            pool_size=settings.POSTGRES_POOL_SIZE,
            max_overflow=settings.POSTGRES_MAX_OVERFLOW,
            pool_pre_ping=True,
        )
        self.async_session = async_sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )

    async def execute(
        self, stmt: Base, no_return: bool = False, return_many: bool = False
    ) -> Any:
        try:
            async with self.async_session() as session:
                cursor: AsyncResult = await session.execute(stmt)  # noqa
                await session.commit()
                if no_return:
                    return None
                if return_many:
                    return cursor.scalars().all()
                return cursor.scalar_one_or_none()
        except (
            IntegrityError,
            OperationalError,
            ProgrammingError,
            InterfaceError,
        ) as err:
            log.error(f"{err.orig}")
        finally:
            await session.close()

    async def select_one(self, stmt: Base) -> Any:
        try:
            async with self.async_session() as session:
                cursor: AsyncResult = await session.execute(stmt)  # noqa
                return cursor.scalar_one_or_none()
        except (OperationalError, ProgrammingError, InterfaceError) as err:
            log.error(f"{err.orig}")
        finally:
            await session.close()

    async def select(self, stmt: Base, no_scalars: bool = False) -> Any:
        try:
            async with self.async_session() as session:
                cursor: AsyncResult = await session.execute(stmt)  # noqa
                if no_scalars:
                    return cursor.all() or None
                return cursor.scalars().all() or None
        except (OperationalError, ProgrammingError, InterfaceError) as err:
            log.error(f"{err.orig}")
        finally:
            await session.close()
