import uuid
from typing import Any

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.envelope import Envelope, pagination_meta
from app.core.pagination import PageParams, get_page_params
from app.modules.identity.deps import get_current_user
from app.modules.identity.models import User
from app.modules.notifications.schemas import NotificationOut
from app.modules.notifications.service import NotificationService

router = APIRouter(prefix="/notifications", tags=["notifications"])


def get_service(session: AsyncSession = Depends(get_session)) -> NotificationService:
    return NotificationService(session)


@router.get("")
async def list_notifications(
    params: PageParams = Depends(get_page_params),
    unread: bool = False,
    current_user: User = Depends(get_current_user),
    service: NotificationService = Depends(get_service),
) -> Envelope[list[NotificationOut]]:
    notifications, total = await service.list_for_user(
        current_user.id, params, unread_only=unread
    )
    return Envelope(
        data=notifications,
        meta=pagination_meta(
            page=params.page,
            page_size=params.page_size,
            total_items=total,
        ),
    )


@router.post("/read-all")
async def mark_all_read(
    current_user: User = Depends(get_current_user),
    service: NotificationService = Depends(get_service),
) -> Envelope[dict[str, Any]]:
    updated = await service.mark_all_read(current_user.id)
    return Envelope(data={"updated": updated})


@router.post("/{notification_id}/read", status_code=status.HTTP_204_NO_CONTENT)
async def mark_read(
    notification_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: NotificationService = Depends(get_service),
) -> None:
    await service.mark_read(notification_id, current_user.id)
