import json
import re
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError, ValidationError
from app.modules.identity.deps import OrgContext
from app.modules.settings.repository import SettingRepository
from app.modules.settings.schemas import SettingOut

PLATFORM_MANAGE = "settings.platform.manage"
ORGANIZATION_MANAGE = "settings.organization.manage"
KEY_PATTERN = re.compile(r"^[a-z0-9_.]{1,100}$")
VALID_SCOPES = ("platform", "organization", "user")


class SettingsService:
    def __init__(self, session: AsyncSession) -> None:
        self.repository = SettingRepository(session)

    async def list(self, scope: str, context: OrgContext) -> list[SettingOut]:
        owner_id = await self._resolve_owner(scope, context)
        settings = await self.repository.list(scope, owner_id)
        return [SettingOut.model_validate(s) for s in settings]

    async def upsert(
        self, scope: str, key: str, value: str, context: OrgContext
    ) -> SettingOut:
        owner_id = await self._resolve_owner(scope, context)
        self._validate_key(key)
        self._validate_value(value)
        setting = await self.repository.upsert(scope, owner_id, key, value)
        return SettingOut.model_validate(setting)

    async def _resolve_owner(self, scope: str, context: OrgContext) -> uuid.UUID | None:
        if scope not in VALID_SCOPES:
            raise ValidationError(
                "Недопустимая область настроек.",
                code="INVALID_SETTING_SCOPE",
            )
        if scope == "platform":
            await self._ensure(context, PLATFORM_MANAGE)
            return None
        if scope == "organization":
            if context.organization_id is None:
                raise AppError(
                    "Для доступа необходимо состоять в организации.",
                    code="NO_ORGANIZATION",
                    status_code=403,
                )
            await self._ensure(context, ORGANIZATION_MANAGE)
            return context.organization_id
        return context.user.id

    async def _ensure(self, context: OrgContext, permission: str) -> None:
        if context.is_platform_admin:
            return
        allowed = await context.rbac.check_user_permission(
            context.user.id, permission, context.organization_id
        )
        if not allowed:
            raise AppError(
                "Недостаточно прав для выполнения действия.",
                code="PERMISSION_DENIED",
                status_code=403,
            )

    def _validate_key(self, key: str) -> None:
        if not KEY_PATTERN.match(key):
            raise ValidationError(
                "Ключ настройки должен соответствовать шаблону [a-z0-9_.] (1–100 символов).",
                code="INVALID_SETTING_KEY",
            )

    def _validate_value(self, value: str) -> None:
        try:
            json.loads(value)
        except (ValueError, TypeError) as exc:
            raise ValidationError(
                "Значение настройки должно быть корректным JSON.",
                code="INVALID_SETTING_VALUE",
            ) from exc
