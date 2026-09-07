import json
import uuid
from datetime import datetime
from typing import Any, TypeVar

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import AuditRecord
from app.core.pagination import PageParams

_RowT = TypeVar("_RowT", bound=tuple[Any, ...])


class AuditRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_page(
        self,
        params: PageParams,
        scope: uuid.UUID | None,
        *,
        user_id: uuid.UUID | None = None,
        entity_type: str | None = None,
        entity_id: uuid.UUID | None = None,
        action_type: str | None = None,
        created_after: datetime | None = None,
        created_before: datetime | None = None,
    ) -> tuple[list[AuditRecord], int]:
        def apply(stmt: Select[_RowT]) -> Select[_RowT]:
            if scope is not None:
                stmt = stmt.where(AuditRecord.organization_id == scope)
            if user_id is not None:
                stmt = stmt.where(AuditRecord.user_id == user_id)
            if entity_type is not None:
                stmt = stmt.where(AuditRecord.entity_type == entity_type)
            if entity_id is not None:
                stmt = stmt.where(AuditRecord.entity_id == entity_id)
            if action_type is not None:
                stmt = stmt.where(AuditRecord.action_type == action_type)
            if created_after is not None:
                stmt = stmt.where(AuditRecord.created_at >= created_after)
            if created_before is not None:
                stmt = stmt.where(AuditRecord.created_at <= created_before)
            return stmt

        query = apply(select(AuditRecord)).order_by(AuditRecord.created_at.desc())
        count_query = apply(select(func.count()).select_from(AuditRecord))
        query = query.limit(params.page_size).offset(params.offset)

        items = await self._session.execute(query)
        total = await self._session.execute(count_query)
        return list(items.scalars().all()), int(total.scalar_one())


def parse_detail(raw: str) -> dict[str, object]:
    try:
        parsed = json.loads(raw)
    except (ValueError, TypeError):
        return {}
    return parsed if isinstance(parsed, dict) else {}
