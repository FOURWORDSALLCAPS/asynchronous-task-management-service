from pydantic import BaseModel, Field
from fastapi import Query

from src.settings import settings


class Pagination(BaseModel):
    total: int = Field(
        description="Общее количество объектов",
        examples=[100],
    )
    page_count: int = Field(
        description="Общее количество страниц",
        examples=[10],
    )


class PaginationParams(BaseModel):
    page: int = Field(
        Query(settings.PAGINATION_PAGE, ge=1, description="Текущий номер страницы")
    )
    page_size: int = Field(
        Query(
            settings.PAGINATION_PAGE_SIZE, ge=1, le=1000, description="Размер страницы"
        )
    )


class BaseQueryPathFilters(PaginationParams):
    count_only: bool = Field(Query(False, description="Только подсчет записей"))
    pagination_on: bool = Field(
        Query(True, description="Pagination включить/выключить")
    )
