from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.envelope import Envelope
from app.modules.identity.deps import OrgContext, get_org_context
from app.modules.settings.schemas import SettingOut, SettingUpsert
from app.modules.settings.service import SettingsService

router = APIRouter(prefix="/settings", tags=["settings"])


def get_service(session: AsyncSession = Depends(get_session)) -> SettingsService:
    return SettingsService(session)


@router.get("")
async def list_settings(
    scope: str = Query(...),
    context: OrgContext = Depends(get_org_context),
    service: SettingsService = Depends(get_service),
) -> Envelope[list[SettingOut]]:
    return Envelope(data=await service.list(scope, context))


@router.put("")
async def upsert_setting(
    data: SettingUpsert,
    context: OrgContext = Depends(get_org_context),
    service: SettingsService = Depends(get_service),
) -> Envelope[SettingOut]:
    return Envelope(data=await service.upsert(data.scope, data.key, data.value, context))
