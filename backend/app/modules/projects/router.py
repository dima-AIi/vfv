import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.envelope import Envelope, pagination_meta
from app.core.errors import AppError
from app.core.pagination import PageParams, get_page_params
from app.modules.crm.service import CustomerService
from app.modules.documents.service import DocumentService
from app.modules.identity.deps import OrgContext, require_permission
from app.modules.projects.schemas import (
    ProjectCreate,
    ProjectMemberAdd,
    ProjectMemberOut,
    ProjectOut,
    ProjectUpdate,
)
from app.modules.projects.service import ProjectService
from app.modules.tasks.service import TaskService

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("")
async def list_projects(
    params: PageParams = Depends(get_page_params),
    status_filter: str | None = None,
    customer_id: uuid.UUID | None = None,
    context: OrgContext = Depends(require_permission("projects.project.read")),
    session: AsyncSession = Depends(get_session),
) -> Envelope[list[ProjectOut]]:
    service = ProjectService(session)
    projects, total = await service.list_projects(
        params=params,
        scope=context.scope,
        status=status_filter,
        customer_id=customer_id,
    )
    return Envelope(
        data=projects,
        meta=pagination_meta(
            page=params.page,
            page_size=params.page_size,
            total_items=total,
        ),
    )


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_project(
    data: ProjectCreate,
    context: OrgContext = Depends(require_permission("projects.project.create")),
    session: AsyncSession = Depends(get_session),
) -> Envelope[ProjectOut]:
    service = ProjectService(session)
    return Envelope(
        data=await service.create_project(data, context.organization_id),
    )


@router.get("/{project_id}")
async def get_project(
    project_id: uuid.UUID,
    context: OrgContext = Depends(require_permission("projects.project.read")),
    session: AsyncSession = Depends(get_session),
) -> Envelope[ProjectOut]:
    service = ProjectService(session)
    return Envelope(data=await service.get_project(project_id, context.scope))


@router.patch("/{project_id}")
async def update_project(
    project_id: uuid.UUID,
    data: ProjectUpdate,
    context: OrgContext = Depends(require_permission("projects.project.update")),
    session: AsyncSession = Depends(get_session),
) -> Envelope[ProjectOut]:
    if "customer_id" in data.model_fields_set and data.customer_id is not None:
        await CustomerService(session).get_model(data.customer_id, context.scope)
    service = ProjectService(session)
    return Envelope(data=await service.update_project(project_id, data, context.scope))


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: uuid.UUID,
    context: OrgContext = Depends(require_permission("projects.project.delete")),
    session: AsyncSession = Depends(get_session),
) -> None:
    service = ProjectService(session)
    await service.get_model(project_id, context.scope)

    task_service = TaskService(session)
    document_service = DocumentService(session)
    tasks = await task_service.count_for_project(project_id, context.scope)
    documents = await document_service.count_for_project(project_id, context.scope)
    if tasks > 0 or documents > 0:
        raise AppError(
            "В проекте есть активные задачи или документы — удалить его нельзя.",
            code="PROJECT_NOT_EMPTY",
            status_code=409,
            details=[{"tasks": tasks, "documents": documents}],
        )
    await service.delete_project(project_id, context.scope)


@router.get("/{project_id}/members")
async def list_project_members(
    project_id: uuid.UUID,
    context: OrgContext = Depends(require_permission("projects.project.read")),
    session: AsyncSession = Depends(get_session),
) -> Envelope[list[ProjectMemberOut]]:
    service = ProjectService(session)
    return Envelope(data=await service.list_members(project_id, context.scope))


@router.post("/{project_id}/members", status_code=status.HTTP_201_CREATED)
async def add_project_member(
    project_id: uuid.UUID,
    data: ProjectMemberAdd,
    context: OrgContext = Depends(require_permission("projects.project.update")),
    session: AsyncSession = Depends(get_session),
) -> Envelope[ProjectMemberOut]:
    service = ProjectService(session)
    return Envelope(data=await service.add_member(project_id, data.user_id, context.scope))


@router.delete("/{project_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_project_member(
    project_id: uuid.UUID,
    user_id: uuid.UUID,
    context: OrgContext = Depends(require_permission("projects.project.update")),
    session: AsyncSession = Depends(get_session),
) -> None:
    service = ProjectService(session)
    await service.remove_member(project_id, user_id, context.scope)
