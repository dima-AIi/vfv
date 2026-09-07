import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import AuditService
from app.core.errors import AppError
from app.modules.identity.schemas import UserOut
from app.modules.identity.service import IdentityService
from app.modules.organizations.models import Organization
from app.modules.organizations.repository import OrganizationRepository
from app.modules.organizations.schemas import (
    MemberOut,
    OrganizationCreate,
    OrganizationMemberOut,
    OrganizationOut,
)
from app.modules.rbac.service import RbacService


class OrganizationService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self.repository = OrganizationRepository(session)
        self.identity_service = IdentityService(session)
        self.rbac_service = RbacService(session)
        self.audit = AuditService(session)

    async def create_organization(
        self,
        *,
        creator_id: uuid.UUID,
        data: OrganizationCreate,
    ) -> OrganizationOut:
        normalized_name = data.name.strip()
        if not normalized_name:
            raise AppError(
                "Название организации не может быть пустым.",
                code="VALIDATION_ERROR",
                status_code=422,
            )
        existing = await self.repository.get_by_name(normalized_name)
        if existing is not None:
            raise AppError(
                "Организация с таким названием уже существует.",
                code="ORGANIZATION_NAME_EXISTS",
                status_code=409,
            )

        organization = await self.repository.create(
            name=normalized_name,
            description=data.description,
            created_by=creator_id,
        )
        await self.identity_service.assign_organization(creator_id, organization.id)
        await self.rbac_service.ensure_user_role(
            user_id=creator_id,
            role_name="org_admin",
            organization_id=organization.id,
        )
        await self.audit.record(
            action_type="ORGANIZATION_CREATED",
            entity_type="organization",
            entity_id=organization.id,
            user_id=creator_id,
            detail={"name": organization.name},
            organization_id=organization.id,
        )
        return OrganizationOut.model_validate(organization)

    async def get_for_member(
        self,
        *,
        user_id: uuid.UUID,
        organization_id: uuid.UUID,
    ) -> OrganizationOut:
        is_member = await self.rbac_service.has_membership(
            user_id=user_id,
            organization_id=organization_id,
        )
        if not is_member:
            raise AppError(
                "Организация не найдена.",
                code="ORGANIZATION_NOT_FOUND",
                status_code=404,
            )
        organization = await self.repository.get(organization_id)
        return OrganizationOut.model_validate(organization)

    async def get_model(self, organization_id: uuid.UUID) -> Organization:
        return await self.repository.get(organization_id)

    async def get_by_id(self, organization_id: uuid.UUID) -> Organization | None:
        return await self.repository.find(organization_id)

    async def list_for_user(self, user_id: uuid.UUID) -> list[OrganizationOut]:
        organization_ids = await self.rbac_service.list_organization_ids(user_id)
        organizations = await self.repository.list_by_ids(organization_ids)
        return [OrganizationOut.model_validate(o) for o in organizations]

    async def invite_user(
        self,
        *,
        actor_id: uuid.UUID,
        organization_id: uuid.UUID,
        email: str,
        display_name: str,
        password: str | None,
    ) -> tuple[uuid.UUID, str | None]:
        await self.rbac_service.ensure_permission(
            actor_id,
            "identity.user.manage",
            organization_id,
        )
        await self.repository.get(organization_id)

        invited, generated_password = await self.identity_service.admin_create_user(
            email=email,
            display_name=display_name,
            password=password,
            organization_id=organization_id,
        )
        await self.rbac_service.ensure_user_role(
            user_id=invited.id,
            role_name="employee",
            organization_id=organization_id,
        )
        await self.audit.record(
            action_type="USER_CREATED_BY_ADMIN",
            entity_type="user",
            entity_id=invited.id,
            user_id=actor_id,
            detail={"email": invited.email, "organization_id": str(organization_id)},
            organization_id=organization_id,
        )
        await self.audit.record(
            action_type="ROLE_ASSIGNED",
            entity_type="user_role",
            entity_id=invited.id,
            user_id=actor_id,
            detail={"role": "employee", "organization_id": str(organization_id)},
            organization_id=organization_id,
        )
        return invited.id, generated_password

    async def list_members(
        self,
        *,
        actor_id: uuid.UUID,
        organization_id: uuid.UUID,
    ) -> list[OrganizationMemberOut]:
        await self.rbac_service.ensure_permission(
            actor_id,
            "identity.user.manage",
            organization_id,
        )
        await self.repository.get(organization_id)
        members = await self.identity_service.list_organization_members(organization_id)
        roles_map = await self.rbac_service.list_org_roles_by_user_ids(
            [member.id for member in members], organization_id
        )
        return [
            OrganizationMemberOut(**member.model_dump(), roles=roles_map.get(member.id, []))
            for member in members
        ]

    async def list_public_members(
        self,
        *,
        user_id: uuid.UUID,
        organization_id: uuid.UUID,
    ) -> list[MemberOut]:
        """Light member list (public fields only) for any member of the organization.

        Non-members receive the same 404 as a missing organization so that the
        endpoint does not disclose existence.
        """
        if not await self.rbac_service.is_platform_admin(user_id):
            is_member = await self.rbac_service.has_membership(
                user_id=user_id,
                organization_id=organization_id,
            )
            if not is_member:
                raise AppError(
                    "Организация не найдена.",
                    code="ORGANIZATION_NOT_FOUND",
                    status_code=404,
                )
        await self.repository.get(organization_id)
        member_ids = await self.rbac_service.list_member_ids(organization_id)
        names = await self.identity_service.get_display_names(member_ids)
        members = [
            MemberOut(id=member_id, display_name=names[member_id])
            for member_id in member_ids
            if member_id in names
        ]
        members.sort(key=lambda member: member.display_name.casefold())
        return members

    async def assign_member_role(
        self,
        *,
        actor_id: uuid.UUID,
        organization_id: uuid.UUID,
        target_user_id: uuid.UUID,
        role_name: str,
    ) -> str:
        await self.rbac_service.ensure_permission(
            actor_id,
            "identity.user.manage",
            organization_id,
        )
        await self.repository.get(organization_id)

        assigned = await self.rbac_service.assign_org_system_role(
            target_user_id=target_user_id,
            organization_id=organization_id,
            role_name=role_name,
        )
        await self.audit.record(
            action_type="ROLE_ASSIGNED",
            entity_type="user_role",
            entity_id=target_user_id,
            user_id=actor_id,
            detail={"role": assigned, "organization_id": str(organization_id)},
            organization_id=organization_id,
        )
        return assigned

    async def set_member_status(
        self,
        *,
        actor_id: uuid.UUID,
        organization_id: uuid.UUID,
        target_user_id: uuid.UUID,
        status: str,
    ) -> UserOut:
        from app.modules.identity.models import USER_STATUSES

        await self.rbac_service.ensure_permission(
            actor_id,
            "identity.user.manage",
            organization_id,
        )
        await self.repository.get(organization_id)
        if status not in USER_STATUSES:
            raise AppError(
                "Недопустимый статус пользователя.",
                code="VALIDATION_ERROR",
                status_code=422,
            )
        target = await self.identity_service.get_public_user(target_user_id)
        if status == "blocked":
            if target_user_id == actor_id:
                raise AppError(
                    "Нельзя заблокировать собственную учётную запись.",
                    code="CANNOT_BLOCK_SELF",
                    status_code=422,
                )
            if await self.rbac_service.is_platform_admin(target_user_id):
                raise AppError(
                    "Администратора платформы нельзя заблокировать через организацию.",
                    code="CANNOT_BLOCK_PLATFORM_ADMIN",
                    status_code=422,
                )
        if target.organization_id != organization_id:
            raise AppError(
                "Пользователь не состоит в этой организации.",
                code="USER_NOT_IN_ORGANIZATION",
                status_code=404,
            )
        old_status = target.status
        await self.identity_service.set_status(target_user_id, status)
        await self.audit.record(
            action_type="USER_STATUS_CHANGED",
            entity_type="user",
            entity_id=target_user_id,
            user_id=actor_id,
            detail={"old_status": old_status, "new_status": status},
            organization_id=organization_id,
        )
        return await self.identity_service.get_user_out(target_user_id)
