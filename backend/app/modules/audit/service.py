import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pagination import PageParams
from app.modules.audit.repository import AuditRepository, parse_detail
from app.modules.audit.schemas import AuditRecordOut


class AuditReadService:
    def __init__(self, session: AsyncSession) -> None:
        self.repository = AuditRepository(session)

    async def list_records(
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
    ) -> tuple[list[AuditRecordOut], int]:
        records, total = await self.repository.list_page(
            params,
            scope,
            user_id=user_id,
            entity_type=entity_type,
            entity_id=entity_id,
            action_type=action_type,
            created_after=created_after,
            created_before=created_before,
        )
        items = [
            AuditRecordOut(
                id=record.id,
                action_type=record.action_type,
                entity_type=record.entity_type,
                entity_id=record.entity_id,
                user_id=record.user_id,
                organization_id=record.organization_id,
                detail=parse_detail(record.detail),
                created_at=record.created_at,
            )
            for record in records
        ]
        return items, total
