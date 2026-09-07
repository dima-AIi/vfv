import uuid

from sqlalchemy import Select, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError, NotFoundError
from app.core.models import utcnow
from app.core.pagination import PageParams
from app.modules.projects.models import Project, ProjectMember
from app.modules.projects.schemas import ProjectCreate, ProjectUpdate


class ProjectRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        data: ProjectCreate,
        organization_id: uuid.UUID | None,
    ) -> Project:
        project = Project(
            name=data.name,
            description=data.description,
            due_date=data.due_date,
            organization_id=organization_id,
        )
        self._session.add(project)
        await self._session.commit()
        await self._session.refresh(project)
        return project

    async def get(
        self,
        project_id: uuid.UUID,
        scope: uuid.UUID | None = None,
    ) -> Project:
        query = select(Project).where(
            Project.id == project_id,
            Project.deleted_at.is_(None),
        )
        if scope is not None:
            query = query.where(Project.organization_id == scope)
        result = await self._session.execute(query)
        project = result.scalar_one_or_none()
        if project is None:
            raise NotFoundError(
                "Проект не найден.",
                code="PROJECT_NOT_FOUND",
            )
        return project

    async def list_visible(
        self,
        params: PageParams,
        scope: uuid.UUID | None,
        status: str | None = None,
        customer_id: uuid.UUID | None = None,
    ) -> tuple[list[Project], int]:
        active = Project.deleted_at.is_(None)
        query: Select[tuple[Project]] = select(Project).where(active)
        count_query: Select[tuple[int]] = (
            select(func.count()).select_from(Project).where(active)
        )
        if scope is not None:
            query = query.where(Project.organization_id == scope)
            count_query = count_query.where(Project.organization_id == scope)
        if status is not None:
            query = query.where(Project.status == status)
            count_query = count_query.where(Project.status == status)
        if customer_id is not None:
            query = query.where(Project.customer_id == customer_id)
            count_query = count_query.where(Project.customer_id == customer_id)

        order = Project.created_at.desc() if params.descending else Project.created_at.asc()
        query = query.order_by(order).limit(params.page_size).offset(params.offset)

        items_result = await self._session.execute(query)
        total_result = await self._session.execute(count_query)
        return list(items_result.scalars().all()), int(total_result.scalar_one())

    async def list_recent(self, limit: int, scope: uuid.UUID | None) -> list[Project]:
        query = (
            select(Project)
            .where(Project.deleted_at.is_(None))
            .order_by(Project.created_at.desc())
            .limit(limit)
        )
        if scope is not None:
            query = query.where(Project.organization_id == scope)
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def count(self, scope: uuid.UUID | None) -> int:
        query = (
            select(func.count()).select_from(Project).where(Project.deleted_at.is_(None))
        )
        if scope is not None:
            query = query.where(Project.organization_id == scope)
        result = await self._session.execute(query)
        return int(result.scalar_one())

    async def update(
        self,
        project_id: uuid.UUID,
        data: ProjectUpdate,
        scope: uuid.UUID | None = None,
    ) -> Project:
        project = await self.get(project_id, scope)
        for field in ("name", "description", "status"):
            value = getattr(data, field)
            if value is not None:
                setattr(project, field, value)
        if "customer_id" in data.model_fields_set:
            project.customer_id = data.customer_id
        if "due_date" in data.model_fields_set:
            project.due_date = data.due_date
        await self._session.commit()
        await self._session.refresh(project)
        return project

    async def soft_delete(self, project_id: uuid.UUID, scope: uuid.UUID | None = None) -> None:
        project = await self.get(project_id, scope)
        project.deleted_at = utcnow()
        await self._session.commit()

    async def get_by_id_any_scope(self, project_id: uuid.UUID) -> Project:
        return await self.get(project_id, None)

    async def search(
        self,
        term: str,
        limit: int,
        scope: uuid.UUID | None = None,
    ) -> list[Project]:
        from app.core.search import LIKE_ESCAPE, like_contains

        pattern = like_contains(term)
        clause = or_(
            func.lower(Project.name).like(pattern, escape=LIKE_ESCAPE),
            func.lower(Project.description).like(pattern, escape=LIKE_ESCAPE),
        )
        query = (
            select(Project)
            .where(Project.deleted_at.is_(None), clause)
            .order_by(Project.created_at.desc())
            .limit(limit)
        )
        if scope is not None:
            query = query.where(Project.organization_id == scope)
        result = await self._session.execute(query)
        return list(result.scalars().all())


class ProjectMemberRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_user_ids(self, project_id: uuid.UUID) -> list[uuid.UUID]:
        result = await self._session.execute(
            select(ProjectMember.user_id)
            .where(ProjectMember.project_id == project_id)
            .order_by(ProjectMember.created_at.asc())
        )
        return [row[0] for row in result.all()]

    async def add(self, project_id: uuid.UUID, user_id: uuid.UUID) -> ProjectMember:
        existing = await self._session.execute(
            select(ProjectMember).where(
                ProjectMember.project_id == project_id,
                ProjectMember.user_id == user_id,
            )
        )
        if existing.scalar_one_or_none() is not None:
            raise AppError(
                "Пользователь уже является участником проекта.",
                code="MEMBER_EXISTS",
                status_code=409,
            )
        member = ProjectMember(project_id=project_id, user_id=user_id)
        self._session.add(member)
        await self._session.commit()
        await self._session.refresh(member)
        return member

    async def remove(self, project_id: uuid.UUID, user_id: uuid.UUID) -> None:
        result = await self._session.execute(
            select(ProjectMember).where(
                ProjectMember.project_id == project_id,
                ProjectMember.user_id == user_id,
            )
        )
        member = result.scalar_one_or_none()
        if member is None:
            raise NotFoundError(
                "Пользователь не является участником проекта.",
                code="MEMBER_NOT_FOUND",
            )
        await self._session.delete(member)
        await self._session.commit()
