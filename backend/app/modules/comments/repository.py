import uuid

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError
from app.core.pagination import PageParams
from app.modules.comments.models import Comment


class CommentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        task_id: uuid.UUID,
        author_id: uuid.UUID | None,
        body: str,
        organization_id: uuid.UUID | None,
    ) -> Comment:
        comment = Comment(
            task_id=task_id,
            author_id=author_id,
            body=body,
            organization_id=organization_id,
        )
        self._session.add(comment)
        await self._session.commit()
        await self._session.refresh(comment)
        return comment

    async def get(
        self,
        comment_id: uuid.UUID,
        scope: uuid.UUID | None = None,
    ) -> Comment:
        query = select(Comment).where(Comment.id == comment_id)
        if scope is not None:
            query = query.where(Comment.organization_id == scope)
        result = await self._session.execute(query)
        comment = result.scalar_one_or_none()
        if comment is None:
            raise NotFoundError(
                "Комментарий не найден.",
                code="COMMENT_NOT_FOUND",
            )
        return comment

    async def list_for_task(
        self,
        task_id: uuid.UUID,
        params: PageParams,
        scope: uuid.UUID | None = None,
    ) -> tuple[list[Comment], int]:
        order = Comment.created_at.desc() if params.descending else Comment.created_at.asc()
        query: Select[tuple[Comment]] = (
            select(Comment)
            .where(Comment.task_id == task_id)
            .order_by(order)
            .limit(params.page_size)
            .offset(params.offset)
        )
        count_query: Select[tuple[int]] = (
            select(func.count()).select_from(Comment).where(Comment.task_id == task_id)
        )
        if scope is not None:
            query = query.where(Comment.organization_id == scope)
            count_query = count_query.where(Comment.organization_id == scope)
        items_result = await self._session.execute(query)
        total_result = await self._session.execute(count_query)
        return list(items_result.scalars().all()), int(total_result.scalar_one())

    async def list_all_for_task(
        self,
        task_id: uuid.UUID,
        scope: uuid.UUID | None = None,
    ) -> list[Comment]:
        query = (
            select(Comment)
            .where(Comment.task_id == task_id)
            .order_by(Comment.created_at.asc())
        )
        if scope is not None:
            query = query.where(Comment.organization_id == scope)
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def delete(self, comment_id: uuid.UUID) -> None:
        comment = await self.get(comment_id)
        await self._session.delete(comment)
        await self._session.commit()
