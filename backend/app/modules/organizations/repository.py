import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError
from app.modules.organizations.models import Organization


class OrganizationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        name: str,
        description: str | None,
        created_by: uuid.UUID | None,
    ) -> Organization:
        organization = Organization(name=name, description=description, created_by=created_by)
        self._session.add(organization)
        await self._session.commit()
        await self._session.refresh(organization)
        return organization

    async def get_by_name(self, name: str) -> Organization | None:
        result = await self._session.execute(
            select(Organization).where(Organization.name == name),
        )
        return result.scalar_one_or_none()

    async def get(self, organization_id: uuid.UUID) -> Organization:
        organization = await self._session.get(Organization, organization_id)
        if organization is None:
            raise NotFoundError(
                "Организация не найдена.",
                code="ORGANIZATION_NOT_FOUND",
            )
        return organization

    async def find(self, organization_id: uuid.UUID) -> Organization | None:
        return await self._session.get(Organization, organization_id)

    async def list_by_ids(self, ids: list[uuid.UUID]) -> list[Organization]:
        if not ids:
            return []
        result = await self._session.execute(
            select(Organization).where(Organization.id.in_(ids)),
        )
        organizations = list(result.scalars().all())
        order = {value: index for index, value in enumerate(ids)}
        organizations.sort(key=lambda item: order.get(item.id, len(order)))
        return organizations
