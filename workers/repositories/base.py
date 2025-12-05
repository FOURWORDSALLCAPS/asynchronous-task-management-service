import sys
import logging
from uuid import UUID
from typing import TypeVar, Generic

from sqlalchemy import insert, select, delete, and_
from sqlalchemy.exc import (
    SQLAlchemyError,
    IntegrityError,
    OperationalError,
    ProgrammingError,
    InterfaceError,
)
from sqlalchemy.orm import InstrumentedAttribute

from engines.postgres_storage import PostgresEngine
from settings import settings

T = TypeVar("T")
log = logging.getLogger(__name__)
stream_handler = logging.StreamHandler(sys.stderr)
stream_handler.setFormatter(logging.Formatter(settings.LOG_FORMAT))
log.addHandler(stream_handler)


class BaseRepository(Generic[T]):
    def __init__(self, db: PostgresEngine, model: type[T]) -> None:
        self.db = db
        self.model = model

    async def get_by(self, **kwargs: str | UUID | bool | set[UUID] | None) -> T | None:
        if not self.model:
            raise ValueError("Model is not defined for this repository")

        if not kwargs:
            raise ValueError("At least one kwargs must be provided")

        try:
            conditions = []
            for field_name, value in kwargs.items():
                field: InstrumentedAttribute = getattr(self.model, field_name, None)
                if field is None:
                    raise ValueError(
                        f"Field '{field_name}' does not exist in {self.model.__name__}"
                    )
                conditions.append(field == value)

            stmt = select(self.model).where(and_(*conditions))

            result = await self.db.execute(stmt)  # noqa

            return result
        except ValueError as e:
            log.error(f"Value error in get_by for {self.model.__name__}: {e}")
            return None
        except (OperationalError, ProgrammingError, InterfaceError) as e:
            log.error(f"Database error in get_by for {self.model.__name__}: {e}")
            return None
        except SQLAlchemyError as e:
            log.error(f"SQLAlchemy error in get_by for {self.model.__name__}: {e}")
            return None
        except Exception as e:
            log.error(f"Unexpected error in get_by for {self.model.__name__}: {e}")
            return None

    async def create(self, **kwargs: str | UUID | bool | set[UUID] | None) -> T | None:
        if not self.model:
            raise ValueError("Model is not defined for this repository")

        try:
            stmt = insert(self.model).values(**kwargs).returning(self.model)

            result = await self.db.execute(stmt)  # noqa

            if result:
                return result
            else:
                log.error(f"Failed to create {self.model.__name__}: no result returned")
                return None
        except IntegrityError as e:
            log.error(f"Integrity error when creating {self.model.__name__}: {e}")
            return None
        except (OperationalError, ProgrammingError, InterfaceError) as e:
            log.error(f"Database error when creating {self.model.__name__}: {e}")
            return None
        except SQLAlchemyError as e:
            log.error(f"SQLAlchemy error when creating {self.model.__name__}: {e}")
            return None
        except Exception as e:
            log.error(f"Unexpected error when creating {self.model.__name__}: {e}")
            return None

    async def delete(self, **filters: str | UUID | bool | set[UUID] | None) -> bool:
        if not self.model:
            raise ValueError("Model is not defined for this repository")

        try:
            stmt = delete(self.model).filter_by(**filters)

            result = await self.db.execute(stmt)  # noqa

            if result.rowcount > 0:
                return True
            else:
                log.warning(
                    f"No {self.model.__name__} records found to delete with filters: {filters}"
                )
                return False
        except IntegrityError as e:
            log.error(f"Integrity error when deleting {self.model.__name__}: {e}")
            return False
        except (OperationalError, ProgrammingError, InterfaceError) as e:
            log.error(f"Database error when deleting {self.model.__name__}: {e}")
            return False
        except SQLAlchemyError as e:
            log.error(f"SQLAlchemy error when deleting {self.model.__name__}: {e}")
            return False
        except Exception as e:
            log.error(f"Unexpected error when deleting {self.model.__name__}: {e}")
            return False
