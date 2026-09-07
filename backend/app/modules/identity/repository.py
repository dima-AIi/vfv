import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError
from app.core.models import utcnow
from app.modules.identity.models import Credential, SessionRecord, User


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, *, email: str, display_name: str) -> User:
        user = User(email=email, display_name=display_name)
        self._session.add(user)
        await self._session.commit()
        await self._session.refresh(user)
        return user

    async def get(self, user_id: uuid.UUID) -> User:
        user = await self._session.get(User, user_id)
        if user is None:
            raise NotFoundError("Пользователь не найден.", code="USER_NOT_FOUND")
        return user

    async def get_by_email(self, email: str) -> User | None:
        result = await self._session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def set_status(self, user_id: uuid.UUID, status: str) -> User:
        user = await self.get(user_id)
        user.status = status
        user.version += 1
        await self._session.commit()
        await self._session.refresh(user)
        return user


class CredentialRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, *, user_id: uuid.UUID, password_hash: str) -> Credential:
        credential = Credential(user_id=user_id, password_hash=password_hash)
        self._session.add(credential)
        await self._session.commit()
        await self._session.refresh(credential)
        return credential

    async def get_for_user(self, user_id: uuid.UUID) -> Credential:
        result = await self._session.execute(
            select(Credential).where(Credential.user_id == user_id),
        )
        credential = result.scalar_one_or_none()
        if credential is None:
            raise NotFoundError(
                "Учётные данные не найдены.",
                code="CREDENTIAL_NOT_FOUND",
            )
        return credential


class SessionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        user_id: uuid.UUID,
        refresh_token_hash: str,
        expires_at: datetime,
    ) -> SessionRecord:
        record = SessionRecord(
            user_id=user_id,
            refresh_token_hash=refresh_token_hash,
            expires_at=expires_at,
            created_at=utcnow(),
            last_used_at=utcnow(),
        )
        self._session.add(record)
        await self._session.commit()
        await self._session.refresh(record)
        return record

    async def get_by_refresh_hash(
        self,
        refresh_token_hash: str,
        *,
        include_revoked: bool = False,
    ) -> SessionRecord | None:
        query = select(SessionRecord).where(
            SessionRecord.refresh_token_hash == refresh_token_hash,
        )
        if not include_revoked:
            query = query.where(SessionRecord.revoked_at.is_(None))
        result = await self._session.execute(query)
        return result.scalar_one_or_none()

    async def get_any_by_refresh_hash(self, refresh_token_hash: str) -> SessionRecord | None:
        return await self.get_by_refresh_hash(refresh_token_hash, include_revoked=True)

    async def revoke(self, record: SessionRecord) -> None:
        if record.revoked_at is None:
            record.revoked_at = utcnow()
            await self._session.commit()

    async def touch(self, record: SessionRecord) -> None:
        record.last_used_at = utcnow()
        await self._session.commit()
