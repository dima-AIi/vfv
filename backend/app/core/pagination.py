from dataclasses import dataclass

from fastapi import Query

from app.core.errors import ValidationError

ALLOWED_SORTS = ("createdAt", "-createdAt")
DEFAULT_SORT = "-createdAt"
DEFAULT_PAGE_SIZE = 25
MAX_PAGE_SIZE = 100


@dataclass(frozen=True)
class PageParams:
    page: int
    page_size: int
    sort: str | None

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size

    @property
    def descending(self) -> bool:
        return self.sort != "createdAt"


def get_page_params(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=DEFAULT_PAGE_SIZE, alias="pageSize"),
    sort: str | None = Query(default=None),
) -> PageParams:
    clamped_page_size = min(MAX_PAGE_SIZE, max(1, page_size))
    if sort is not None and sort not in ALLOWED_SORTS:
        raise ValidationError(
            "Недопустимый параметр сортировки.",
            code="INVALID_SORT",
        )
    return PageParams(page=page, page_size=clamped_page_size, sort=sort)
