import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pagination import PageParams
from app.modules.notifications.repository import NotificationRepository
from app.modules.notifications.schemas import NotificationOut


class NotificationService:
    def __init__(self, session: AsyncSession) -> None:
        self.repository = NotificationRepository(session)

    async def create(
        self,
        *,
        user_id: uuid.UUID,
        organization_id: uuid.UUID | None,
        title: str,
        body: str,
        entity_type: str,
        entity_id: uuid.UUID | None,
    ) -> NotificationOut:
        notification = await self.repository.create(
            user_id=user_id,
            organization_id=organization_id,
            title=title,
            body=body,
            entity_type=entity_type,
            entity_id=entity_id,
        )
        return NotificationOut.model_validate(notification)

    async def list_for_user(
        self,
        user_id: uuid.UUID,
        params: PageParams,
        unread_only: bool = False,
    ) -> tuple[list[NotificationOut], int]:
        notifications, total = await self.repository.list_for_user(user_id, params, unread_only)
        return [NotificationOut.model_validate(n) for n in notifications], total

    async def mark_read(self, notification_id: uuid.UUID, user_id: uuid.UUID) -> None:
        await self.repository.mark_read(notification_id, user_id)

    async def mark_all_read(self, user_id: uuid.UUID) -> int:
        return await self.repository.mark_all_read(user_id)
