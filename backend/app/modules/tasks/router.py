import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.envelope import Envelope, pagination_meta
from app.core.pagination import PageParams, get_page_params
from app.modules.comments.service import CommentService
from app.modules.identity.deps import OrgContext, require_permission
from app.modules.tasks.schemas import (
    TaskAttachmentAdd,
    TaskAttachmentOut,
    TaskCreate,
    TaskDetail,
    TaskOut,
    TaskUpdate,
)
from app.modules.tasks.service import TaskService

router = APIRouter(prefix="/tasks", tags=["tasks"])


def get_service(session: AsyncSession = Depends(get_session)) -> TaskService:
    return TaskService(session)


def get_comment_service(session: AsyncSession = Depends(get_session)) -> CommentService:
    return CommentService(session)


@router.get("")
async def list_tasks(
    project_id: uuid.UUID,
    params: PageParams = Depends(get_page_params),
    context: OrgContext = Depends(require_permission("tasks.task.read")),
    service: TaskService = Depends(get_service),
) -> Envelope[list[TaskOut]]:
    tasks, total = await service.list_tasks_for_project(
        project_id,
        params,
        context.scope,
    )
    return Envelope(
        data=tasks,
        meta=pagination_meta(
            page=params.page,
            page_size=params.page_size,
            total_items=total,
        ),
    )


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_task(
    data: TaskCreate,
    context: OrgContext = Depends(require_permission("tasks.task.create")),
    service: TaskService = Depends(get_service),
) -> Envelope[TaskOut]:
    return Envelope(data=await service.create_task(data, context.organization_id))


@router.get("/{task_id}")
async def get_task(
    task_id: uuid.UUID,
    context: OrgContext = Depends(require_permission("tasks.task.read")),
    service: TaskService = Depends(get_service),
    comment_service: CommentService = Depends(get_comment_service),
) -> Envelope[TaskDetail]:
    task = await service.get_task(task_id, context.scope)
    comments = await comment_service.list_all_for_task(task_id, context.scope)
    attachments = await service.list_attachments(task_id, context.scope)
    detail = TaskDetail(**task.model_dump(), comments=comments, attachments=attachments)
    return Envelope(data=detail)


@router.get("/{task_id}/attachments")
async def list_attachments(
    task_id: uuid.UUID,
    context: OrgContext = Depends(require_permission("tasks.task.read")),
    service: TaskService = Depends(get_service),
) -> Envelope[list[TaskAttachmentOut]]:
    return Envelope(data=await service.list_attachments(task_id, context.scope))


@router.post("/{task_id}/attachments", status_code=status.HTTP_201_CREATED)
async def add_attachment(
    task_id: uuid.UUID,
    data: TaskAttachmentAdd,
    context: OrgContext = Depends(require_permission("tasks.task.update")),
    service: TaskService = Depends(get_service),
) -> Envelope[TaskAttachmentOut]:
    return Envelope(data=await service.add_attachment(task_id, data.file_id, context))


@router.delete("/{task_id}/attachments/{attachment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_attachment(
    task_id: uuid.UUID,
    attachment_id: uuid.UUID,
    context: OrgContext = Depends(require_permission("tasks.task.update")),
    service: TaskService = Depends(get_service),
) -> None:
    await service.delete_attachment(task_id, attachment_id, context)


@router.patch("/{task_id}")
async def update_task(
    task_id: uuid.UUID,
    data: TaskUpdate,
    context: OrgContext = Depends(require_permission("tasks.task.update")),
    service: TaskService = Depends(get_service),
) -> Envelope[TaskOut]:
    return Envelope(data=await service.update_task(task_id, data, context.scope))


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: uuid.UUID,
    context: OrgContext = Depends(require_permission("tasks.task.delete")),
    service: TaskService = Depends(get_service),
) -> None:
    await service.delete_task(task_id, context.scope)
