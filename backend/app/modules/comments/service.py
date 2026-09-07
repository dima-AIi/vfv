import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.core.pagination import PageParams
from app.modules.comments.events import publish_comment_created
from app.modules.comments.models import Comment
from app.modules.comments.repository import CommentRepository
from app.modules.comments.schemas import CommentCreate, CommentOut
from app.modules.identity.deps import OrgContext
from app.modules.identity.service import IdentityService
from app.modules.tasks.service import TaskService

COMMENT_DELETE_PERMISSION = "comments.comment.delete"


class CommentService:
    def __init__(self, session: AsyncSession) -> None:
        self.repository = CommentRepository(session)
        self.task_service = TaskService(session)
        self.identity_service = IdentityService(session)

    async def create_comment(
        self,
        task_id: uuid.UUID,
        data: CommentCreate,
        context: OrgContext,
    ) -> CommentOut:
        task = await self.task_service.get_model(task_id, context.scope)
        comment = await self.repository.create(
            task_id=task.id,
            author_id=context.user.id,
            body=data.body,
            organization_id=task.organization_id,
        )
        await publish_comment_created(comment, task)
        return await self._to_out(comment)

    async def list_comments(
        self,
        task_id: uuid.UUID,
        params: PageParams,
        scope: uuid.UUID | None = None,
    ) -> tuple[list[CommentOut], int]:
        await self.task_service.get_model(task_id, scope)
        comments, total = await self.repository.list_for_task(task_id, params, scope)
        return await self._to_out_list(comments), total

    async def list_all_for_task(
        self,
        task_id: uuid.UUID,
        scope: uuid.UUID | None = None,
    ) -> list[CommentOut]:
        comments = await self.repository.list_all_for_task(task_id, scope)
        return await self._to_out_list(comments)

    async def delete_comment(self, comment_id: uuid.UUID, context: OrgContext) -> None:
        comment = await self.repository.get(comment_id, context.scope)
        if comment.author_id == context.user.id:
            await self.repository.delete(comment_id)
            return
        allowed = context.is_platform_admin or await context.rbac.check_user_permission(
            context.user.id,
            COMMENT_DELETE_PERMISSION,
            comment.organization_id,
        )
        if not allowed:
            raise AppError(
                "Удалить комментарий может только его автор или пользователь с правом удаления.",
                code="COMMENT_DELETE_FORBIDDEN",
                status_code=403,
            )
        await self.repository.delete(comment_id)

    async def _to_out(self, comment: Comment) -> CommentOut:
        out = CommentOut.model_validate(comment)
        if comment.author_id is not None:
            names = await self.identity_service.get_display_names([comment.author_id])
            out.author_name = names.get(comment.author_id)
        return out

    async def _to_out_list(self, comments: list[Comment]) -> list[CommentOut]:
        author_ids = list({c.author_id for c in comments if c.author_id is not None})
        names = await self.identity_service.get_display_names(author_ids)
        outs: list[CommentOut] = []
        for comment in comments:
            out = CommentOut.model_validate(comment)
            if comment.author_id is not None:
                out.author_name = names.get(comment.author_id)
            outs.append(out)
        return outs
