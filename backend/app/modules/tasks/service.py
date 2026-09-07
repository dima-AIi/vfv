import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError, NotFoundError, ValidationError
from app.core.pagination import PageParams
from app.modules.files.service import FileService
from app.modules.identity.deps import OrgContext
from app.modules.identity.service import IdentityService
from app.modules.projects.service import ProjectService
from app.modules.tasks.events import (
    publish_task_assigned,
    publish_task_completed,
    publish_task_created,
)
from app.modules.tasks.models import Task
from app.modules.tasks.repository import TaskAttachmentRepository, TaskRepository
from app.modules.tasks.schemas import (
    TASK_PRIORITIES,
    TASK_STATUSES,
    TaskAttachmentOut,
    TaskCreate,
    TaskOut,
    TaskSearchResult,
    TaskUpdate,
)


class TaskService:
    def __init__(self, session: AsyncSession) -> None:
        self.project_service = ProjectService(session)
        self.identity_service = IdentityService(session)
        self.task_repository = TaskRepository(session)
        self.attachment_repository = TaskAttachmentRepository(session)
        self.file_service = FileService(session)

    async def create_task(
        self,
        data: TaskCreate,
        organization_id: uuid.UUID | None = None,
    ) -> TaskOut:
        project = await self.project_service.get_model(data.project_id, organization_id)
        if data.status not in TASK_STATUSES:
            raise ValidationError(
                "Недопустимый статус задачи.",
            )
        if data.priority not in TASK_PRIORITIES:
            raise ValidationError(
                "Недопустимый приоритет задачи.",
            )
        if data.assignee_id is not None:
            await self._ensure_assignee_in_org(data.assignee_id, project.organization_id)
        task = await self.task_repository.create(
            data,
            project.organization_id,
        )
        await publish_task_created(task)
        if task.assignee_id is not None:
            await publish_task_assigned(task)
        return await self._to_out(task)

    async def get_task(self, task_id: uuid.UUID, scope: uuid.UUID | None = None) -> TaskOut:
        task = await self.task_repository.get(task_id, scope)
        return await self._to_out(task)

    async def get_model(self, task_id: uuid.UUID, scope: uuid.UUID | None = None) -> Task:
        return await self.task_repository.get(task_id, scope)

    async def list_tasks_for_project(
        self,
        project_id: uuid.UUID,
        params: PageParams,
        scope: uuid.UUID | None = None,
    ) -> tuple[list[TaskOut], int]:
        await self.project_service.get_model(project_id, scope)
        tasks, total = await self.task_repository.list_for_project(project_id, params, scope)
        outs = [await self._to_out(task) for task in tasks]
        return outs, total

    async def list_recent(
        self,
        limit: int = 5,
        scope: uuid.UUID | None = None,
    ) -> list[TaskOut]:
        tasks = await self.task_repository.list_recent(limit, scope)
        return [await self._to_out(task) for task in tasks]

    async def count(self, scope: uuid.UUID | None = None) -> int:
        return await self.task_repository.count(scope)

    async def count_for_project(
        self,
        project_id: uuid.UUID,
        scope: uuid.UUID | None = None,
    ) -> int:
        return await self.task_repository.count_for_project(project_id, scope)

    async def search(
        self,
        term: str,
        limit: int,
        scope: uuid.UUID | None = None,
    ) -> list[TaskSearchResult]:
        tasks = await self.task_repository.search(term, limit, scope)
        return [TaskSearchResult.model_validate(t) for t in tasks]

    async def update_task(
        self,
        task_id: uuid.UUID,
        data: TaskUpdate,
        scope: uuid.UUID | None = None,
    ) -> TaskOut:
        validation_messages = {
            "status": "Недопустимый статус задачи.",
            "priority": "Недопустимый приоритет задачи.",
        }
        for field, allowed in (("status", TASK_STATUSES), ("priority", TASK_PRIORITIES)):
            value = getattr(data, field)
            if value is not None and value not in allowed:
                raise ValidationError(validation_messages[field])
        current = await self.task_repository.get(task_id, scope)
        previous_status = current.status
        previous_assignee_id = current.assignee_id
        if data.assignee_id is not None:
            await self._ensure_assignee_in_org(data.assignee_id, current.organization_id)
        task = await self.task_repository.update(task_id, data, scope)
        if task.assignee_id is not None and task.assignee_id != previous_assignee_id:
            await publish_task_assigned(task)
        if task.status == "done" and previous_status != "done":
            await publish_task_completed(task)
        return await self._to_out(task)

    async def delete_task(self, task_id: uuid.UUID, scope: uuid.UUID | None = None) -> None:
        await self.task_repository.soft_delete(task_id, scope)

    async def list_attachments(
        self, task_id: uuid.UUID, scope: uuid.UUID | None = None
    ) -> list[TaskAttachmentOut]:
        await self.task_repository.get(task_id, scope)
        attachments = await self.attachment_repository.list_for_task(task_id)
        creator_ids = [a.created_by for a in attachments if a.created_by is not None]
        names = await self.identity_service.get_display_names(list(set(creator_ids)))
        results: list[TaskAttachmentOut] = []
        for attachment in attachments:
            try:
                file_out = await self.file_service.get_file(attachment.file_id, scope)
            except AppError:
                continue
            results.append(
                TaskAttachmentOut(
                    id=attachment.id,
                    file_id=attachment.file_id,
                    filename=file_out.filename,
                    mime_type=file_out.mime_type,
                    size_bytes=file_out.size_bytes,
                    created_at=attachment.created_at,
                    created_by_name=names.get(attachment.created_by)
                    if attachment.created_by is not None
                    else None,
                )
            )
        return results

    async def add_attachment(
        self, task_id: uuid.UUID, file_id: uuid.UUID, context: OrgContext
    ) -> TaskAttachmentOut:
        task = await self.task_repository.get(task_id, context.scope)
        file_out = await self.file_service.get_file(file_id, context.scope)
        attachment = await self.attachment_repository.add(
            task.id, file_out.id, context.user.id
        )
        names = await self.identity_service.get_display_names([context.user.id])
        return TaskAttachmentOut(
            id=attachment.id,
            file_id=attachment.file_id,
            filename=file_out.filename,
            mime_type=file_out.mime_type,
            size_bytes=file_out.size_bytes,
            created_at=attachment.created_at,
            created_by_name=names.get(context.user.id),
        )

    async def delete_attachment(
        self, task_id: uuid.UUID, attachment_id: uuid.UUID, context: OrgContext
    ) -> None:
        task = await self.task_repository.get(task_id, context.scope)
        attachment = await self.attachment_repository.get(attachment_id)
        if attachment.task_id != task.id:
            raise NotFoundError(
                "Вложение не найдено.",
                code="ATTACHMENT_NOT_FOUND",
            )
        if attachment.created_by != context.user.id:
            allowed = context.is_platform_admin or await context.rbac.check_user_permission(
                context.user.id, "tasks.task.delete", task.organization_id
            )
            if not allowed:
                raise AppError(
                    "Удалить вложение может только его создатель"
                    " или пользователь с правом удаления.",
                    code="ATTACHMENT_DELETE_FORBIDDEN",
                    status_code=403,
                )
        await self.attachment_repository.remove(attachment)

    async def _ensure_assignee_in_org(
        self,
        assignee_id: uuid.UUID,
        organization_id: uuid.UUID | None,
    ) -> None:
        user = await self.identity_service.get_public_user(assignee_id)
        if user.organization_id != organization_id:
            raise ValidationError(
                "Исполнитель должен состоять в организации задачи.",
                code="ASSIGNEE_NOT_IN_ORG",
            )

    async def _to_out(self, task: Task) -> TaskOut:
        out = TaskOut.model_validate(task)
        if task.assignee_id is not None:
            names = await self.identity_service.get_display_names([task.assignee_id])
            out.assignee_name = names.get(task.assignee_id)
        return out
