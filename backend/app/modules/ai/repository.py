import uuid

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.errors import NotFoundError
from app.core.models import utcnow
from app.core.pagination import PageParams
from app.modules.ai.models import AIAction, AIResult
from app.modules.ai.schemas import AIActionCreate, AIActionDetail, AIActionOut, AIResultOut


class AIRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_action(
        self,
        data: AIActionCreate,
        provider: str,
        organization_id: uuid.UUID | None,
    ) -> AIAction:
        action = AIAction(
            project_id=data.project_id,
            task_id=data.task_id,
            action_type=data.action_type,
            input_text=data.input_text,
            provider=provider,
            status="pending",
            organization_id=organization_id,
        )
        self._session.add(action)
        await self._session.commit()
        await self._session.refresh(action)
        return action

    async def save_result(
        self,
        action_id: uuid.UUID,
        content: str,
        summary: str,
    ) -> AIResult:
        result = AIResult(action_id=action_id, content=content, summary=summary)
        self._session.add(result)
        await self._session.commit()
        await self._session.refresh(result)
        return result

    async def complete_action(
        self,
        action: AIAction,
        context_summary: str,
    ) -> AIAction:
        action.status = "completed"
        action.context_summary = context_summary
        action.completed_at = utcnow()
        await self._session.commit()
        await self._session.refresh(action)
        return action

    async def fail_action(self, action: AIAction, message: str) -> AIAction:
        action.status = "failed"
        action.error = message[:2000]
        action.completed_at = utcnow()
        await self._session.commit()
        await self._session.refresh(action)
        return action

    async def get_detail(
        self,
        action_id: uuid.UUID,
        scope: uuid.UUID | None = None,
    ) -> AIActionDetail:
        query = (
            select(AIAction)
            .where(AIAction.id == action_id)
            .options(selectinload(AIAction.result))
        )
        if scope is not None:
            query = query.where(AIAction.organization_id == scope)
        result = await self._session.execute(query)
        action = result.scalar_one_or_none()
        if action is None:
            raise NotFoundError(f"AI action {action_id} not found.", code="AI_ACTION_NOT_FOUND")
        return self.to_detail(action)

    async def list_for_project(
        self,
        project_id: uuid.UUID | None,
        params: PageParams,
        scope: uuid.UUID | None = None,
    ) -> tuple[list[AIAction], int]:
        order = AIAction.created_at.desc() if params.descending else AIAction.created_at.asc()
        query: Select[tuple[AIAction]] = (
            select(AIAction)
            .order_by(order)
            .limit(params.page_size)
            .offset(params.offset)
            .options(selectinload(AIAction.result))
        )
        count_query: Select[tuple[int]] = select(func.count()).select_from(AIAction)
        if scope is not None:
            query = query.where(AIAction.organization_id == scope)
            count_query = count_query.where(AIAction.organization_id == scope)
        if project_id is not None:
            query = query.where(AIAction.project_id == project_id)
            count_query = count_query.where(AIAction.project_id == project_id)
        items_result = await self._session.execute(query)
        total_result = await self._session.execute(count_query)
        return list(items_result.scalars().all()), int(total_result.scalar_one())

    async def list_recent(self, limit: int, scope: uuid.UUID | None) -> list[AIAction]:
        query = (
            select(AIAction)
            .order_by(AIAction.created_at.desc())
            .limit(limit)
            .options(selectinload(AIAction.result))
        )
        if scope is not None:
            query = query.where(AIAction.organization_id == scope)
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def count(self, scope: uuid.UUID | None = None) -> int:
        query = select(func.count()).select_from(AIAction)
        if scope is not None:
            query = query.where(AIAction.organization_id == scope)
        result = await self._session.execute(query)
        return int(result.scalar_one())

    @staticmethod
    def to_detail(action: AIAction) -> AIActionDetail:
        detail = AIActionDetail(**AIActionOut.model_validate(action).model_dump())
        if action.result:
            detail.result = AIResultOut.model_validate(action.result[0])
        return detail
