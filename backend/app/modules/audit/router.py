import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.envelope import Envelope, pagination_meta
from app.core.pagination import PageParams, get_page_params
from app.modules.audit.schemas import AuditRecordOut
from app.modules.audit.service import AuditReadService
from app.modules.identity.deps import OrgContext, require_permission

router = APIRouter(prefix="/audit", tags=["audit"])


def get_service(session: AsyncSession = Depends(get_session)) -> AuditReadService:
    return AuditReadService(session)


@router.get("")
async def list_audit(
    params: PageParams = Depends(get_page_params),
    user_id: uuid.UUID | None = None,
    entity_type: str | None = None,
    entity_id: uuid.UUID | None = None,
    action_type: str | None = None,
    created_after: datetime | None = Query(default=None, alias="createdAfter"),
    created_before: datetime | None = Query(default=None, alias="createdBefore"),
    context: OrgContext = Depends(require_permission("audit.record.read")),
    service: AuditReadService = Depends(get_service),
) -> Envelope[list[AuditRecordOut]]:
    records, total = await service.list_records(
        params,
        context.scope,
        user_id=user_id,
        entity_type=entity_type,
        entity_id=entity_id,
        action_type=action_type,
        created_after=created_after,
        created_before=created_before,
    )
    return Envelope(
        data=records,
        meta=pagination_meta(
            page=params.page, page_size=params.page_size, total_items=total
        ),
    )
