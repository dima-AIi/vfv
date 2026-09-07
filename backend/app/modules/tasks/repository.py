import uuid

from sqlalchemy import Select, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError, NotFoundError
from app.core.models import utcnow
from app.core.pagination import PageParams
from app.core.search import LIKE_ESCAPE, like_contains
from app.modules.tasks.models import Task, TaskAttachment
from app.modules.tasks.schemas import TaskCreate, TaskUpdate


class TaskRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        data: TaskCreate,
        organization_id: uuid.UUID | None,
    ) -> Task:
        task = Task(
            project_id=data.project_id,
            title=data.title,
            description=data.description,
            status=data.status,
            priority=data.priority,
            due_date=data.due_date,
            assignee_id=data.assignee_id,
            organization_id=organization_id,
        )
        self._session.add(task)
        await self._session.commit()
        await self._session.refresh(task)
        return task

    async def get(
        self,
        task_id: uuid.UUID,
        scope: uuid.UUID | None = None,
    ) -> Task:
        query = select(Task).where(
            Task.id == task_id,
            Task.deleted_at.is_(None),
        )
        if scope is not None:
            query = query.where(Task.organization_id == scope)
        result = await self._session.execute(query)
        task = result.scalar_one_or_none()
        if task is None:
            raise NotFoundError("Задача не найдена.", code="TASK_NOT_FOUND")
        return task

    async def list_for_project(
        self,
        project_id: uuid.UUID,
        params: PageParams,
        scope: uuid.UUID | None = None,
    ) -> tuple[list[Task], int]:
        active = Task.deleted_at.is_(None)
        order = Task.created_at.desc() if params.descending else Task.created_at.asc()
        query: Select[tuple[Task]] = (
            select(Task)
            .where(Task.project_id == project_id, active)
            .order_by(order)
            .limit(params.page_size)
            .offset(params.offset)
        )
        count_query: Select[tuple[int]] = (
            select(func.count())
            .select_from(Task)
            .where(Task.project_id == project_id, active)
        )
        if scope is not None:
            query = query.where(Task.organization_id == scope)
            count_query = count_query.where(Task.organization_id == scope)
        items_result = await self._session.execute(query)
        total_result = await self._session.execute(count_query)
        return list(items_result.scalars().all()), int(total_result.scalar_one())

    async def list_recent(self, limit: int, scope: uuid.UUID | None) -> list[Task]:
        query = (
            select(Task)
            .where(Task.deleted_at.is_(None))
            .order_by(Task.created_at.desc())
            .limit(limit)
        )
        if scope is not None:
            query = query.where(Task.organization_id == scope)
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def count(self, scope: uuid.UUID | None = None) -> int:
        query = (
            select(func.count()).select_from(Task).where(Task.deleted_at.is_(None))
        )
        if scope is not None:
            query = query.where(Task.organization_id == scope)
        result = await self._session.execute(query)
        return int(result.scalar_one())

    async def count_for_project(
        self,
        project_id: uuid.UUID,
        scope: uuid.UUID | None = None,
    ) -> int:
        query = (
            select(func.count())
            .select_from(Task)
            .where(Task.project_id == project_id, Task.deleted_at.is_(None))
        )
        if scope is not None:
            query = query.where(Task.organization_id == scope)
        result = await self._session.execute(query)
        return int(result.scalar_one())

    async def update(
        self,
        task_id: uuid.UUID,
        data: TaskUpdate,
        scope: uuid.UUID | None = None,
    ) -> Task:
        task = await self.get(task_id, scope)
        for field in ("title", "description", "status", "priority", "due_date", "assignee_id"):
            value = getattr(data, field)
            if value is not None:
                setattr(task, field, value)
        await self._session.commit()
        await self._session.refresh(task)
        return task

    async def soft_delete(self, task_id: uuid.UUID, scope: uuid.UUID | None = None) -> None:
        task = await self.get(task_id, scope)
        task.deleted_at = utcnow()
        await self._session.commit()

    async def search(
        self,
        term: str,
        limit: int,
        scope: uuid.UUID | None = None,
    ) -> list[Task]:
        pattern = like_contains(term)
        clause = or_(
            func.lower(Task.title).like(pattern, escape=LIKE_ESCAPE),
            func.lower(Task.description).like(pattern, escape=LIKE_ESCAPE),
        )
        query = (
            select(Task)
            .where(Task.deleted_at.is_(None), clause)
            .order_by(Task.created_at.desc())
            .limit(limit)
        )
        if scope is not None:
            query = query.where(Task.organization_id == scope)
        result = await self._session.execute(query)
        return list(result.scalars().all())


class TaskAttachmentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_for_task(self, task_id: uuid.UUID) -> list[TaskAttachment]:
        result = await self._session.execute(
            select(TaskAttachment)
            .where(TaskAttachment.task_id == task_id)
            .order_by(TaskAttachment.created_at.asc())
        )
        return list(result.scalars().all())

    async def get(self, attachment_id: uuid.UUID) -> TaskAttachment:
        result = await self._session.execute(
            select(TaskAttachment).where(TaskAttachment.id == attachment_id)
        )
        attachment = result.scalar_one_or_none()
        if attachment is None:
            raise NotFoundError(
                "Вложение не найдено.",
                code="ATTACHMENT_NOT_FOUND",
            )
        return attachment

    async def add(
        self, task_id: uuid.UUID, file_id: uuid.UUID, created_by: uuid.UUID | None
    ) -> TaskAttachment:
        existing = await self._session.execute(
            select(TaskAttachment).where(
                TaskAttachment.task_id == task_id,
                TaskAttachment.file_id == file_id,
            )
        )
        if existing.scalar_one_or_none() is not None:
            raise AppError(
                "Этот файл уже прикреплён к задаче.",
                code="ATTACHMENT_EXISTS",
                status_code=409,
            )
        attachment = TaskAttachment(task_id=task_id, file_id=file_id, created_by=created_by)
        self._session.add(attachment)
        await self._session.commit()
        await self._session.refresh(attachment)
        return attachment

    async def remove(self, attachment: TaskAttachment) -> None:
        await self._session.delete(attachment)
        await self._session.commit()
