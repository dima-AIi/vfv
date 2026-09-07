import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.envelope import Envelope, pagination_meta
from app.core.pagination import PageParams, get_page_params
from app.modules.comments.schemas import CommentCreate, CommentOut
from app.modules.comments.service import CommentService
from app.modules.identity.deps import OrgContext, require_permission

router = APIRouter(tags=["comments"])


def get_service(session: AsyncSession = Depends(get_session)) -> CommentService:
    return CommentService(session)


@router.post("/tasks/{task_id}/comments", status_code=status.HTTP_201_CREATED)
async def create_comment(
    task_id: uuid.UUID,
    data: CommentCreate,
    context: OrgContext = Depends(require_permission("tasks.task.read")),
    service: CommentService = Depends(get_service),
) -> Envelope[CommentOut]:
    return Envelope(data=await service.create_comment(task_id, data, context))


@router.get("/tasks/{task_id}/comments")
async def list_comments(
    task_id: uuid.UUID,
    params: PageParams = Depends(get_page_params),
    context: OrgContext = Depends(require_permission("tasks.task.read")),
    service: CommentService = Depends(get_service),
) -> Envelope[list[CommentOut]]:
    comments, total = await service.list_comments(task_id, params, context.scope)
    return Envelope(
        data=comments,
        meta=pagination_meta(
            page=params.page,
            page_size=params.page_size,
            total_items=total,
        ),
    )


@router.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    comment_id: uuid.UUID,
    context: OrgContext = Depends(require_permission("tasks.task.read")),
    service: CommentService = Depends(get_service),
) -> None:
    await service.delete_comment(comment_id, context)
