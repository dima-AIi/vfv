import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.settings.models import Setting


class SettingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list(self, scope: str, owner_id: uuid.UUID | None) -> list[Setting]:
        query = select(Setting).where(Setting.scope == scope)
        if owner_id is None:
            query = query.where(Setting.owner_id.is_(None))
        else:
            query = query.where(Setting.owner_id == owner_id)
        result = await self._session.execute(query.order_by(Setting.key.asc()))
        return list(result.scalars().all())

    async def upsert(
        self, scope: str, owner_id: uuid.UUID | None, key: str, value: str
    ) -> Setting:
        query = select(Setting).where(Setting.scope == scope, Setting.key == key)
        if owner_id is None:
            query = query.where(Setting.owner_id.is_(None))
        else:
            query = query.where(Setting.owner_id == owner_id)
        result = await self._session.execute(query)
        existing = result.scalar_one_or_none()
        if existing is not None:
            existing.value = value
            await self._session.commit()
            await self._session.refresh(existing)
            return existing
        setting = Setting(scope=scope, owner_id=owner_id, key=key, value=value)
        self._session.add(setting)
        await self._session.commit()
        await self._session.refresh(setting)
        return setting
