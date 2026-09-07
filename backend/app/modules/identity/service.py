import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import AuditService
from app.core.config import settings
from app.core.errors import AppError
from app.core.models import ensure_utc
from app.core.security import (
    create_access_token,
    generate_refresh_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)
from app.modules.identity.models import SessionRecord, User
from app.modules.identity.repository import CredentialRepository, SessionRepository, UserRepository
from app.modules.identity.schemas import (
    PASSWORD_MIN_LENGTH,
    AuthOut,
    LoginIn,
    RegisterIn,
    TokenPairOut,
    UserOut,
)

AUDIT_ENTITY = "user"
SESSION_ENTITY = "session"


class IdentityService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self.users = UserRepository(session)
        self.credentials = CredentialRepository(session)
        self.sessions = SessionRepository(session)
        self.audit = AuditService(session)

    async def register(self, data: RegisterIn) -> UserOut:
        if len(data.password) < PASSWORD_MIN_LENGTH:
            raise AppError(
                f"Пароль должен содержать не менее {PASSWORD_MIN_LENGTH} символов.",
                code="PASSWORD_TOO_WEAK",
                status_code=422,
            )
        existing = await self.users.get_by_email(data.email)
        if existing is not None:
            raise AppError(
                "Email уже зарегистрирован.",
                code="EMAIL_ALREADY_EXISTS",
                status_code=409,
            )

        user = await self.users.create(email=data.email, display_name=data.display_name)
        await self.credentials.create(user_id=user.id, password_hash=hash_password(data.password))
        await self.audit.record(
            action_type="USER_REGISTERED",
            entity_type=AUDIT_ENTITY,
            entity_id=user.id,
            user_id=user.id,
            detail={"email": user.email},
        )
        return UserOut.model_validate(user)

    async def login(self, data: LoginIn) -> AuthOut:
        user = await self.users.get_by_email(data.email)
        invalid = AppError(
            "Неверный email или пароль.",
            code="AUTH_INVALID_CREDENTIALS",
            status_code=401,
        )
        if user is None:
            hash_password(data.password)  # constant-ish work to avoid user enumeration timing
            raise invalid
        credential = await self.credentials.get_for_user(user.id)
        if not verify_password(data.password, credential.password_hash):
            await self.audit.record(
                action_type="LOGIN_FAILED",
                entity_type=AUDIT_ENTITY,
                user_id=user.id,
                detail={"reason": "invalid_credentials"},
                organization_id=user.organization_id,
            )
            raise invalid
        if user.status == "blocked":
            await self.audit.record(
                action_type="LOGIN_FAILED",
                entity_type=AUDIT_ENTITY,
                user_id=user.id,
                detail={"reason": "user_blocked"},
                organization_id=user.organization_id,
            )
            raise AppError(
                "Учётная запись заблокирована.",
                code="USER_BLOCKED",
                status_code=403,
            )

        auth = await self._issue_session(user)
        await self.audit.record(
            action_type="LOGIN_SUCCESS",
            entity_type=AUDIT_ENTITY,
            entity_id=user.id,
            user_id=user.id,
            detail={},
            organization_id=user.organization_id,
        )
        return auth

    async def refresh(self, refresh_token: str) -> AuthOut:
        token_hash = hash_refresh_token(refresh_token)
        session_record = await self.sessions.get_any_by_refresh_hash(token_hash)
        if session_record is None:
            raise AppError(
                "Refresh-токен не распознан.",
                code="INVALID_REFRESH_TOKEN",
                status_code=401,
            )
        if session_record.revoked_at is not None:
            raise AppError(
                "Сессия уже отозвана.",
                code="SESSION_REVOKED",
                status_code=401,
            )
        if ensure_utc(session_record.expires_at) < datetime.now(UTC):
            raise AppError(
                "Срок действия сессии истёк.",
                code="SESSION_EXPIRED",
                status_code=401,
            )

        user = await self.users.get(session_record.user_id)
        if user.status == "blocked":
            await self.sessions.revoke(session_record)
            raise AppError(
                "Учётная запись заблокирована.",
                code="USER_BLOCKED",
                status_code=403,
            )

        await self.sessions.revoke(session_record)
        auth = await self._issue_session(user)
        return auth

    async def logout(self, session_id: uuid.UUID | None, user: User) -> None:
        if session_id is None:
            return
        rows = await self._session.execute(
            select(SessionRecord).where(SessionRecord.id == session_id),
        )
        session_record = rows.scalar_one_or_none()
        if (
            session_record is not None
            and session_record.user_id == user.id
            and session_record.revoked_at is None
        ):
            await self.sessions.revoke(session_record)
            await self.audit.record(
                action_type="LOGOUT",
                entity_type=SESSION_ENTITY,
                entity_id=session_record.id,
                user_id=user.id,
                detail={},
                organization_id=user.organization_id,
            )

    async def _issue_session(self, user: User) -> AuthOut:
        refresh_token, refresh_hash = generate_refresh_token()
        expires_at = datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days)
        session_record = await self.sessions.create(
            user_id=user.id,
            refresh_token_hash=refresh_hash,
            expires_at=expires_at,
        )
        access_token = create_access_token(
            user_id=user.id,
            email=user.email,
            session_id=session_record.id,
        )
        return AuthOut(
            user=UserOut.model_validate(user),
            tokens=TokenPairOut(access_token=access_token, refresh_token=refresh_token),
        )

    async def assign_organization(
        self,
        user_id: uuid.UUID,
        organization_id: uuid.UUID | None,
    ) -> UserOut:
        user = await self.users.get(user_id)
        user.organization_id = organization_id
        user.version += 1
        await self._session.commit()
        await self._session.refresh(user)
        return UserOut.model_validate(user)

    async def set_status(self, user_id: uuid.UUID, status_value: str) -> None:
        from app.modules.identity.models import USER_STATUSES

        if status_value not in USER_STATUSES:
            raise AppError(
                f"Статус должен быть одним из: {', '.join(USER_STATUSES)}.",
                code="VALIDATION_ERROR",
                status_code=422,
            )
        await self.users.set_status(user_id, status_value)

    async def admin_create_user(
        self,
        *,
        email: str,
        display_name: str,
        password: str | None,
        organization_id: uuid.UUID,
    ) -> tuple[UserOut, str | None]:
        normalized_email = email.strip().lower()
        existing = await self.users.get_by_email(normalized_email)
        if existing is not None:
            raise AppError(
                "Email уже зарегистрирован.",
                code="EMAIL_ALREADY_EXISTS",
                status_code=409,
            )

        generated_password: str | None = None
        if password is None:
            import secrets

            generated_password = secrets.token_urlsafe(12)
            effective_password = generated_password
        else:
            if len(password) < PASSWORD_MIN_LENGTH:
                raise AppError(
                    f"Пароль должен содержать не менее {PASSWORD_MIN_LENGTH} символов.",
                    code="PASSWORD_TOO_WEAK",
                    status_code=422,
                )
            effective_password = password

        user = await self.users.create(
            email=normalized_email,
            display_name=display_name,
        )
        user.organization_id = organization_id
        await self._session.commit()
        await self._session.refresh(user)

        await self.credentials.create(
            user_id=user.id,
            password_hash=hash_password(effective_password),
        )
        return UserOut.model_validate(user), generated_password

    async def list_organization_members(self, organization_id: uuid.UUID) -> list[UserOut]:
        result = await self._session.execute(
            select(User).where(User.organization_id == organization_id),
        )
        return [UserOut.model_validate(u) for u in result.scalars().all()]

    async def get_user_out(self, user_id: uuid.UUID) -> UserOut:
        user = await self.users.get(user_id)
        return UserOut.model_validate(user)

    async def get_public_user(self, user_id: uuid.UUID) -> UserOut:
        """Public read of a single user (public fields only)."""
        user = await self.users.get(user_id)
        return UserOut.model_validate(user)

    async def get_display_names(self, user_ids: list[uuid.UUID]) -> dict[uuid.UUID, str]:
        """Map of user id -> display_name for the given ids (public field only)."""
        if not user_ids:
            return {}
        result = await self._session.execute(
            select(User.id, User.display_name).where(User.id.in_(user_ids)),
        )
        return {row[0]: row[1] for row in result.all()}

    async def list_public_users(self, user_ids: list[uuid.UUID]) -> list[UserOut]:
        """Batch public read of users by ids (public fields only), preserving order."""
        if not user_ids:
            return []
        result = await self._session.execute(select(User).where(User.id.in_(user_ids)))
        by_id = {user.id: user for user in result.scalars().all()}
        return [UserOut.model_validate(by_id[uid]) for uid in user_ids if uid in by_id]
