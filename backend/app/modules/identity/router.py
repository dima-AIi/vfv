import uuid

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.envelope import Envelope
from app.modules.identity.deps import get_current_user
from app.modules.identity.models import User
from app.modules.identity.schemas import (
    AuthOut,
    LoginIn,
    MeOut,
    RefreshIn,
    RegisterIn,
    UserOut,
)
from app.modules.identity.service import IdentityService
from app.modules.organizations.service import OrganizationService
from app.modules.rbac.service import RbacService

router = APIRouter(prefix="/auth", tags=["auth"])


def get_service(session: AsyncSession = Depends(get_session)) -> IdentityService:
    return IdentityService(session)


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    data: RegisterIn,
    service: IdentityService = Depends(get_service),
) -> Envelope[UserOut]:
    return Envelope(data=await service.register(data))


@router.post("/login")
async def login(
    data: LoginIn,
    service: IdentityService = Depends(get_service),
) -> Envelope[AuthOut]:
    return Envelope(data=await service.login(data))


@router.post("/refresh")
async def refresh(
    data: RefreshIn,
    service: IdentityService = Depends(get_service),
) -> Envelope[AuthOut]:
    return Envelope(data=await service.refresh(data.refresh_token))


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    request: Request,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> None:
    payload = getattr(request.state, "token_payload", {})
    raw_sid = payload.get("sid") if isinstance(payload, dict) else None
    session_id: uuid.UUID | None = None
    if isinstance(raw_sid, str):
        try:
            session_id = uuid.UUID(raw_sid)
        except ValueError:
            session_id = None
    await IdentityService(session).logout(session_id, current_user)


@router.get("/me")
async def me(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> Envelope[MeOut]:
    rbac_service = RbacService(session)
    organization_service = OrganizationService(session)

    roles = await rbac_service.list_role_codes(current_user.id)
    organization_brief = None
    if current_user.organization_id is not None:
        organization = await organization_service.get_by_id(current_user.organization_id)
        if organization is not None:
            from app.modules.identity.schemas import OrganizationBrief

            organization_brief = OrganizationBrief(
                id=organization.id,
                name=organization.name,
            )

    me_out = MeOut(**UserOut.model_validate(current_user).model_dump())
    me_out.organization = organization_brief
    me_out.roles = roles
    return Envelope(data=me_out)
