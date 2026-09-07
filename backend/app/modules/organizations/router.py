import uuid

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.envelope import Envelope, pagination_meta
from app.modules.identity.deps import get_current_user
from app.modules.identity.models import User
from app.modules.identity.schemas import UserOut
from app.modules.organizations.schemas import (
    AssignRoleIn,
    InvitedUserOut,
    InviteUserIn,
    MemberOut,
    OrganizationCreate,
    OrganizationMemberOut,
    OrganizationOut,
    UserStatusIn,
)
from app.modules.organizations.service import OrganizationService

router = APIRouter(prefix="/organizations", tags=["organizations"])


def get_service(session: AsyncSession = Depends(get_session)) -> OrganizationService:
    return OrganizationService(session)


class OrganizationListOut(BaseModel):
    items: list[OrganizationOut]
    total: int


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_organization(
    data: OrganizationCreate,
    current_user: User = Depends(get_current_user),
    service: OrganizationService = Depends(get_service),
) -> Envelope[OrganizationOut]:
    organization = await service.create_organization(
        creator_id=current_user.id,
        data=data,
    )
    return Envelope(data=organization)


@router.get("")
async def list_organizations(
    page: int = 1,
    page_size: int = 25,
    current_user: User = Depends(get_current_user),
    service: OrganizationService = Depends(get_service),
) -> Envelope[list[OrganizationOut]]:
    organizations = await service.list_for_user(current_user.id)
    total = len(organizations)
    safe_page_size = max(1, min(page_size, 100))
    safe_page = max(1, page)
    start = (safe_page - 1) * safe_page_size
    end = start + safe_page_size
    return Envelope(
        data=organizations[start:end],
        meta=pagination_meta(
            page=safe_page,
            page_size=safe_page_size,
            total_items=total,
        ),
    )


@router.get("/{organization_id}")
async def get_organization(
    organization_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: OrganizationService = Depends(get_service),
) -> Envelope[OrganizationOut]:
    organization = await service.get_for_member(
        user_id=current_user.id,
        organization_id=organization_id,
    )
    return Envelope(data=organization)


@router.post("/{organization_id}/users", status_code=status.HTTP_201_CREATED)
async def invite_user(
    organization_id: uuid.UUID,
    data: InviteUserIn,
    current_user: User = Depends(get_current_user),
    service: OrganizationService = Depends(get_service),
) -> Envelope[InvitedUserOut]:
    invited_id, generated_password = await service.invite_user(
        actor_id=current_user.id,
        organization_id=organization_id,
        email=data.email,
        display_name=data.display_name,
        password=data.password,
    )
    invited_out = await service.identity_service.get_user_out(invited_id)
    payload = InvitedUserOut(
        id=invited_out.id,
        email=invited_out.email,
        display_name=invited_out.display_name,
        organization_id=organization_id,
        generated_password=generated_password,
    )
    return Envelope(data=payload)


@router.get("/{organization_id}/users")
async def list_members(
    organization_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    page: int = 1,
    page_size: int = 25,
    service: OrganizationService = Depends(get_service),
) -> Envelope[list[OrganizationMemberOut]]:
    members = await service.list_members(
        actor_id=current_user.id,
        organization_id=organization_id,
    )
    total = len(members)
    safe_page_size = max(1, min(page_size, 100))
    safe_page = max(1, page)
    start = (safe_page - 1) * safe_page_size
    end = start + safe_page_size
    return Envelope(
        data=members[start:end],
        meta=pagination_meta(
            page=safe_page,
            page_size=safe_page_size,
            total_items=total,
        ),
    )


@router.get("/{organization_id}/members")
async def list_public_members(
    organization_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: OrganizationService = Depends(get_service),
) -> Envelope[list[MemberOut]]:
    members = await service.list_public_members(
        user_id=current_user.id,
        organization_id=organization_id,
    )
    return Envelope(data=members)


@router.patch("/{organization_id}/users/{user_id}/role")
async def assign_member_role(
    organization_id: uuid.UUID,
    user_id: uuid.UUID,
    data: AssignRoleIn,
    current_user: User = Depends(get_current_user),
    service: OrganizationService = Depends(get_service),
) -> Envelope[UserOut]:
    await service.assign_member_role(
        actor_id=current_user.id,
        organization_id=organization_id,
        target_user_id=user_id,
        role_name=data.role.strip().lower(),
    )
    updated_user = await service.identity_service.get_user_out(user_id)
    return Envelope(data=updated_user)


@router.patch("/{organization_id}/users/{user_id}/status")
async def set_member_status(
    organization_id: uuid.UUID,
    user_id: uuid.UUID,
    data: UserStatusIn,
    current_user: User = Depends(get_current_user),
    service: OrganizationService = Depends(get_service),
) -> Envelope[UserOut]:
    updated = await service.set_member_status(
        actor_id=current_user.id,
        organization_id=organization_id,
        target_user_id=user_id,
        status=data.status.strip().lower(),
    )
    return Envelope(data=updated)
