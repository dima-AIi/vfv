import uuid
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.errors import AppError
from app.core.security import decode_access_token
from app.modules.identity.models import User
from app.modules.identity.repository import UserRepository
from app.modules.rbac.service import RbacService


async def get_current_user(
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> User:
    authorization = request.headers.get("Authorization")
    if authorization is None or not authorization.startswith("Bearer "):
        raise AppError(
            "Требуется авторизация.",
            code="INVALID_TOKEN",
            status_code=401,
        )
    token = authorization.removeprefix("Bearer ").strip()

    payload = decode_access_token(token)
    request.state.token_payload = payload
    raw_user_id = payload.get("sub")
    if not isinstance(raw_user_id, str):
        raise AppError("Недействительный субъект токена.", code="INVALID_TOKEN", status_code=401)
    try:
        user_id = uuid.UUID(raw_user_id)
    except ValueError as exc:
        raise AppError(
            "Недействительный субъект токена.", code="INVALID_TOKEN", status_code=401
        ) from exc

    repository = UserRepository(session)
    user = await repository.get(user_id)
    if user.status == "blocked":
        raise AppError("Пользователь заблокирован.", code="USER_BLOCKED", status_code=403)
    return user


@dataclass(frozen=True)
class OrgContext:
    user: User
    organization_id: uuid.UUID | None
    is_platform_admin: bool
    rbac: RbacService

    @property
    def scope(self) -> uuid.UUID | None:
        """None = unrestricted (platform admin); organization id for tenants."""
        return None if self.is_platform_admin else self.organization_id


async def get_org_context(
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> OrgContext:
    user = await get_current_user(request, session)
    rbac = RbacService(session)
    is_admin = await rbac.is_platform_admin(user.id)
    return OrgContext(
        user=user,
        organization_id=user.organization_id,
        is_platform_admin=is_admin,
        rbac=rbac,
    )


def require_permission(
    code: str,
) -> Callable[[Request, AsyncSession], Awaitable[OrgContext]]:
    async def dependency(
        request: Request,
        session: AsyncSession = Depends(get_session),
    ) -> OrgContext:
        context = await get_org_context(request, session)
        if context.is_platform_admin:
            return context
        if context.organization_id is None:
            raise AppError(
                "Для доступа необходимо состоять в организации.",
                code="NO_ORGANIZATION",
                status_code=403,
            )
        allowed = await context.rbac.check_user_permission(
            context.user.id,
            code,
            context.organization_id,
        )
        if not allowed:
            raise AppError(
                "Недостаточно прав для выполнения действия.",
                code="PERMISSION_DENIED",
                status_code=403,
            )
        return context

    return dependency
