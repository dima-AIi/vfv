import uuid

from sqlalchemy import Select, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError
from app.core.models import utcnow
from app.core.pagination import PageParams
from app.modules.notifications.models import Notification


class NotificationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        user_id: uuid.UUID,
        organization_id: uuid.UUID | None,
        title: str,
        body: str,
        entity_type: str,
        entity_id: uuid.UUID | None,
    ) -> Notification:
        notification = Notification(
            user_id=user_id,
            organization_id=organization_id,
            title=title[:200],
            body=body[:2000],
            entity_type=entity_type[:50],
            entity_id=entity_id,
        )
        self._session.add(notification)
        await self._session.commit()
        await self._session.refresh(notification)
        return notification

    async def list_for_user(
        self,
        user_id: uuid.UUID,
        params: PageParams,
        unread_only: bool = False,
    ) -> tuple[list[Notification], int]:
        base = select(Notification).where(Notification.user_id == user_id)
        count_base = (
            select(func.count()).select_from(Notification).where(Notification.user_id == user_id)
        )
        if unread_only:
            base = base.where(Notification.read_at.is_(None))
            count_base = count_base.where(Notification.read_at.is_(None))
        query: Select[tuple[Notification]] = (
            base.order_by(Notification.created_at.desc())
            .limit(params.page_size)
            .offset(params.offset)
        )
        items_result = await self._session.execute(query)
        total_result = await self._session.execute(count_base)
        return list(items_result.scalars().all()), int(total_result.scalar_one())

    async def get_for_user(self, notification_id: uuid.UUID, user_id: uuid.UUID) -> Notification:
        result = await self._session.execute(
            select(Notification).where(
                Notification.id == notification_id,
                Notification.user_id == user_id,
            ),
        )
        notification = result.scalar_one_or_none()
        if notification is None:
            raise NotFoundError(
                f"Уведомление {notification_id} не найдено.",
                code="NOTIFICATION_NOT_FOUND",
            )
        return notification

    async def mark_read(self, notification_id: uuid.UUID, user_id: uuid.UUID) -> None:
        notification = await self.get_for_user(notification_id, user_id)
        if notification.read_at is None:
            notification.read_at = utcnow()
            await self._session.commit()

    async def mark_all_read(self, user_id: uuid.UUID) -> int:
        count_result = await self._session.execute(
            select(func.count())
            .select_from(Notification)
            .where(Notification.user_id == user_id, Notification.read_at.is_(None))
        )
        unread = int(count_result.scalar_one())
        if unread > 0:
            await self._session.execute(
                update(Notification)
                .where(Notification.user_id == user_id, Notification.read_at.is_(None))
                .values(read_at=utcnow())
            )
            await self._session.commit()
        return unread
