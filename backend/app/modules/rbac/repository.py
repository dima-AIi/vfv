import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.rbac.models import Permission, Role, RolePermission, UserRole


class RbacRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_role_by_name(self, name: str) -> Role | None:
        result = await self._session.execute(select(Role).where(Role.name == name))
        return result.scalar_one_or_none()

    async def list_system_roles(self) -> list[Role]:
        result = await self._session.execute(
            select(Role).where(Role.is_system.is_(True)).order_by(Role.name),
        )
        return list(result.scalars().all())

    async def add_user_role(
        self,
        *,
        user_id: uuid.UUID,
        role_id: uuid.UUID,
        organization_id: uuid.UUID | None,
    ) -> UserRole:
        user_role = UserRole(
            user_id=user_id,
            role_id=role_id,
            organization_id=organization_id,
        )
        self._session.add(user_role)
        await self._session.commit()
        await self._session.refresh(user_role)
        return user_role

    async def find_user_role(
        self,
        *,
        user_id: uuid.UUID,
        role_id: uuid.UUID,
        organization_id: uuid.UUID | None,
    ) -> UserRole | None:
        query = select(UserRole).where(
            UserRole.user_id == user_id,
            UserRole.role_id == role_id,
        )
        if organization_id is None:
            query = query.where(UserRole.organization_id.is_(None))
        else:
            query = query.where(UserRole.organization_id == organization_id)
        result = await self._session.execute(query)
        return result.scalar_one_or_none()

    async def permission_holds(
        self,
        *,
        user_id: uuid.UUID,
        code: str,
        organization_id: uuid.UUID | None,
    ) -> bool:
        query = (
            select(Permission.id)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .join(UserRole, UserRole.role_id == RolePermission.role_id)
            .where(
                Permission.code == code,
                UserRole.user_id == user_id,
            )
        )
        if organization_id is None:
            query = query.where(UserRole.organization_id.is_(None))
        else:
            from sqlalchemy import or_

            query = query.where(
                or_(
                    UserRole.organization_id.is_(None),
                    UserRole.organization_id == organization_id,
                ),
            )
        result = await self._session.execute(query.limit(1))
        return result.scalar_one_or_none() is not None

    async def list_role_codes_for_user(self, user_id: uuid.UUID) -> list[str]:
        result = await self._session.execute(
            select(Role.name)
            .join(UserRole, UserRole.role_id == Role.id)
            .where(UserRole.user_id == user_id)
            .order_by(Role.name),
        )
        return [row[0] for row in result.all()]

    async def list_organization_ids_for_user(self, user_id: uuid.UUID) -> list[uuid.UUID]:
        result = await self._session.execute(
            select(UserRole.organization_id)
            .where(UserRole.user_id == user_id)
            .where(UserRole.organization_id.is_not(None)),
        )
        return [row[0] for row in result.all()]

    async def has_platform_role(self, user_id: uuid.UUID, role_name: str) -> bool:
        result = await self._session.execute(
            select(UserRole.id)
            .join(Role, Role.id == UserRole.role_id)
            .where(
                UserRole.user_id == user_id,
                Role.name == role_name,
                UserRole.organization_id.is_(None),
            ),
        )
        return result.scalar_one_or_none() is not None

    async def has_organization_membership(
        self,
        *,
        user_id: uuid.UUID,
        organization_id: uuid.UUID,
    ) -> bool:
        result = await self._session.execute(
            select(UserRole.id).where(
                UserRole.user_id == user_id,
                UserRole.organization_id == organization_id,
            ),
        )
        return result.scalar_one_or_none() is not None

    async def replace_org_roles_for_user(
        self,
        *,
        user_id: uuid.UUID,
        organization_id: uuid.UUID,
        new_role_id: uuid.UUID,
    ) -> None:
        current = await self._session.execute(
            select(UserRole).where(
                UserRole.user_id == user_id,
                UserRole.organization_id == organization_id,
            ),
        )
        for record in current.scalars().all():
            await self._session.delete(record)
        await self._session.flush()
        await self.add_user_role(
            user_id=user_id,
            role_id=new_role_id,
            organization_id=organization_id,
        )

    async def list_member_user_ids(self, organization_id: uuid.UUID) -> list[uuid.UUID]:
        result = await self._session.execute(
            select(UserRole.user_id)
            .where(UserRole.organization_id == organization_id)
            .distinct(),
        )
        return [row[0] for row in result.all()]

    async def list_org_role_names_by_users(
        self, user_ids: list[uuid.UUID], organization_id: uuid.UUID
    ) -> dict[uuid.UUID, list[str]]:
        """Batch org-scoped role names per user (platform roles excluded: org_id NULL)."""
        if not user_ids:
            return {}
        result = await self._session.execute(
            select(UserRole.user_id, Role.name)
            .join(Role, Role.id == UserRole.role_id)
            .where(
                UserRole.user_id.in_(user_ids),
                UserRole.organization_id == organization_id,
            )
            .order_by(Role.name)
        )
        grouped: dict[uuid.UUID, list[str]] = {}
        for user_id, role_name in result.all():
            grouped.setdefault(user_id, []).append(role_name)
        return grouped
