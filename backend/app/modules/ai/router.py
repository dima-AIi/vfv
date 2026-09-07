import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.envelope import Envelope, pagination_meta
from app.core.pagination import PageParams, get_page_params
from app.modules.ai.schemas import AIActionCreate, AIActionDetail
from app.modules.ai.service import AIService
from app.modules.identity.deps import OrgContext, require_permission

router = APIRouter(prefix="/ai", tags=["ai"])


def get_service(session: AsyncSession = Depends(get_session)) -> AIService:
    return AIService(session)


class ProviderInfoOut(BaseModel):
    active: str
    registered: list[str]


@router.get("/providers")
async def providers(
    context: OrgContext = Depends(require_permission("ai.action.read")),
) -> Envelope[ProviderInfoOut]:
    from app.modules.ai.registry import get_provider, registered_providers

    return Envelope(
        data=ProviderInfoOut(active=get_provider().name, registered=registered_providers()),
    )


@router.post("/actions")
async def run_action(
    data: AIActionCreate,
    context: OrgContext = Depends(require_permission("ai.action.run")),
    service: AIService = Depends(get_service),
) -> Envelope[AIActionDetail]:
    return Envelope(data=await service.run_action(data, context.organization_id))


@router.get("/actions")
async def list_actions(
    params: PageParams = Depends(get_page_params),
    project_id: uuid.UUID | None = None,
    context: OrgContext = Depends(require_permission("ai.action.read")),
    service: AIService = Depends(get_service),
) -> Envelope[list[AIActionDetail]]:
    actions, total = await service.list_actions(
        params=params,
        project_id=project_id,
        scope=context.scope,
    )
    return Envelope(
        data=actions,
        meta=pagination_meta(
            page=params.page,
            page_size=params.page_size,
            total_items=total,
        ),
    )


@router.get("/actions/{action_id}")
async def get_action(
    action_id: uuid.UUID,
    context: OrgContext = Depends(require_permission("ai.action.read")),
    service: AIService = Depends(get_service),
) -> Envelope[AIActionDetail]:
    return Envelope(data=await service.get_action(action_id, context.scope))
