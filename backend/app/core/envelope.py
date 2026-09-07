import math
from typing import Any

from pydantic import BaseModel, Field


class Envelope[EnvelopeData](BaseModel):
    data: EnvelopeData
    meta: dict[str, Any] = Field(default_factory=dict)
    links: dict[str, Any] = Field(default_factory=dict)


class PaginationMeta(BaseModel):
    page: int
    pageSize: int
    totalItems: int
    totalPages: int
    hasNext: bool
    hasPrevious: bool


def pagination_meta(*, page: int, page_size: int, total_items: int) -> dict[str, Any]:
    total_pages = math.ceil(total_items / page_size) if total_items > 0 else 0
    return {
        "pagination": {
            "page": page,
            "pageSize": page_size,
            "totalItems": total_items,
            "totalPages": total_pages,
            "hasNext": page < total_pages,
            "hasPrevious": page > 1 and total_items > 0,
        },
    }
