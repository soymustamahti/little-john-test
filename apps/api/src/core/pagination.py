from dataclasses import dataclass
from math import ceil
from typing import Annotated, Generic, TypeVar

from fastapi import Query
from pydantic import BaseModel, Field

DEFAULT_PAGE_SIZE = 10
MAX_PAGE_SIZE = 100


class PaginationParams(BaseModel):
    page: Annotated[int, Field(ge=1)] = 1
    page_size: Annotated[int, Field(ge=1, le=MAX_PAGE_SIZE)] = DEFAULT_PAGE_SIZE

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


def get_pagination_params(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
) -> PaginationParams:
    return PaginationParams(page=page, page_size=page_size)


ItemT = TypeVar("ItemT")


@dataclass(frozen=True)
class PaginatedResult(Generic[ItemT]):
    items: list[ItemT]
    total_items: int


class PaginatedResponse(BaseModel, Generic[ItemT]):
    items: list[ItemT]
    page: Annotated[int, Field(ge=1)]
    page_size: Annotated[int, Field(ge=1, le=MAX_PAGE_SIZE)]
    total_items: Annotated[int, Field(ge=0)]
    total_pages: Annotated[int, Field(ge=0)]


def build_paginated_response(
    *,
    items: list[ItemT],
    pagination: PaginationParams,
    total_items: int,
) -> PaginatedResponse[ItemT]:
    total_pages = ceil(total_items / pagination.page_size) if total_items else 0
    return PaginatedResponse[ItemT](
        items=items,
        page=pagination.page,
        page_size=pagination.page_size,
        total_items=total_items,
        total_pages=total_pages,
    )
