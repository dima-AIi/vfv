import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError, NotFoundError
from app.modules.rbac.models import Role
from app.modules.rbac.repository import RbacRepository
from app.modules.rbac.seed import ASSIGNABLE_ORG_ROLES


class RbacService:
    def __init__(self, session: AsyncSession) -> None:
        self.repository = RbacRepository(session)

    async def check_user_permission(
        self,
        user_id: uuid.UUID,
        code: str,
        organization_id: uuid.UUID | None = None,
    ) -> bool:
        return await self.repository.permission_holds(
            user_id=user_id,
            code=code,
            organization_id=organization_id,
        )

    async def ensure_permission(
        self,
        user_id: uuid.UUID,
        code: str,
        organization_id: uuid.UUID | None = None,
    ) -> None:
        if not await self.check_user_permission(user_id, code, organization_id):
            raise AppError(
                "Недостаточно прав для выполнения действия.",
                code="PERMISSION_DENIED",
                status_code=403,
            )

    async def ensure_user_role(
        self,
        *,
        user_id: uuid.UUID,
        role_name: str,
        organization_id: uuid.UUID | None,
    ) -> None:
        role = await self._require_role(role_name)
        existing = await self.repository.find_user_role(
            user_id=user_id,
            role_id=role.id,
            organization_id=organization_id,
        )
        if existing is None:
            await self.repository.add_user_role(
                user_id=user_id,
                role_id=role.id,
                organization_id=organization_id,
            )

    async def assign_org_system_role(
        self,
        *,
        target_user_id: uuid.UUID,
        organization_id: uuid.UUID,
        role_name: str,
    ) -> str:
        role = await self._require_role(role_name)
        if role_name not in ASSIGNABLE_ORG_ROLES:
            raise AppError(
                "Эту системную роль нельзя назначать в рамках организации.",
                code="ROLE_ASSIGNMENT_FORBIDDEN",
                status_code=422,
            )

        held_in_org = await self.repository.has_organization_membership(
            user_id=target_user_id,
            organization_id=organization_id,
        )
        if not held_in_org:
            raise NotFoundError(
                "Пользователь не состоит в этой организации.",
                code="USER_NOT_IN_ORGANIZATION",
            )

        await self.repository.replace_org_roles_for_user(
            user_id=target_user_id,
            organization_id=organization_id,
            new_role_id=role.id,
        )
        return role_name

    async def is_platform_admin(self, user_id: uuid.UUID) -> bool:
        return await self.repository.has_platform_role(user_id, "platform_admin")

    async def list_role_codes(self, user_id: uuid.UUID) -> list[str]:
        return await self.repository.list_role_codes_for_user(user_id)

    async def list_organization_ids(self, user_id: uuid.UUID) -> list[uuid.UUID]:
        return await self.repository.list_organization_ids_for_user(user_id)

    async def has_membership(self, *, user_id: uuid.UUID, organization_id: uuid.UUID) -> bool:
        return await self.repository.has_organization_membership(
            user_id=user_id,
            organization_id=organization_id,
        )

    async def list_member_ids(self, organization_id: uuid.UUID) -> list[uuid.UUID]:
        return await self.repository.list_member_user_ids(organization_id)

    async def list_org_roles_by_user_ids(
        self, user_ids: list[uuid.UUID], organization_id: uuid.UUID
    ) -> dict[uuid.UUID, list[str]]:
        """Batch current organization-scoped roles per user (no N+1)."""
        return await self.repository.list_org_role_names_by_users(user_ids, organization_id)

    async def _require_role(self, name: str) -> Role:
        role = await self.repository.get_role_by_name(name)
        if role is None:
            raise NotFoundError("Роль не найдена.", code="ROLE_NOT_FOUND")
        return role
