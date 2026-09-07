import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError, ValidationError
from app.core.pagination import PageParams
from app.modules.identity.service import IdentityService
from app.modules.projects.models import Project
from app.modules.projects.repository import ProjectMemberRepository, ProjectRepository
from app.modules.projects.schemas import (
    ProjectCreate,
    ProjectMemberOut,
    ProjectOut,
    ProjectSearchResult,
    ProjectUpdate,
)

ALLOWED_STATUSES = frozenset({"active", "archived"})


class ProjectService:
    def __init__(self, session: AsyncSession) -> None:
        self.repository = ProjectRepository(session)
        self.member_repository = ProjectMemberRepository(session)
        self.identity_service = IdentityService(session)

    async def create_project(
        self,
        data: ProjectCreate,
        organization_id: uuid.UUID | None,
    ) -> ProjectOut:
        project = await self.repository.create(data, organization_id)
        return ProjectOut.model_validate(project)

    async def get_project(
        self,
        project_id: uuid.UUID,
        scope: uuid.UUID | None = None,
    ) -> ProjectOut:
        project = await self.repository.get(project_id, scope)
        return ProjectOut.model_validate(project)

    async def get_model(
        self,
        project_id: uuid.UUID,
        scope: uuid.UUID | None = None,
    ) -> Project:
        return await self.repository.get(project_id, scope)

    async def list_projects(
        self,
        params: PageParams,
        scope: uuid.UUID | None = None,
        status: str | None = None,
        customer_id: uuid.UUID | None = None,
    ) -> tuple[list[ProjectOut], int]:
        projects, total = await self.repository.list_visible(
            params=params,
            scope=scope,
            status=status,
            customer_id=customer_id,
        )
        return [ProjectOut.model_validate(p) for p in projects], total

    async def list_recent(
        self,
        limit: int = 5,
        scope: uuid.UUID | None = None,
    ) -> list[ProjectOut]:
        projects = await self.repository.list_recent(limit, scope)
        return [ProjectOut.model_validate(p) for p in projects]

    async def count(self, scope: uuid.UUID | None = None) -> int:
        return await self.repository.count(scope)

    async def search(
        self,
        term: str,
        limit: int,
        scope: uuid.UUID | None = None,
    ) -> list[ProjectSearchResult]:
        projects = await self.repository.search(term, limit, scope)
        return [ProjectSearchResult.model_validate(p) for p in projects]

    async def update_project(
        self,
        project_id: uuid.UUID,
        data: ProjectUpdate,
        scope: uuid.UUID | None = None,
    ) -> ProjectOut:
        if data.status is not None and data.status not in ALLOWED_STATUSES:
            raise ValidationError(
                "Недопустимый статус проекта.",
            )
        project = await self.repository.update(project_id, data, scope)
        return ProjectOut.model_validate(project)

    async def delete_project(
        self,
        project_id: uuid.UUID,
        scope: uuid.UUID | None = None,
    ) -> None:
        await self.repository.soft_delete(project_id, scope)

    async def list_members(
        self, project_id: uuid.UUID, scope: uuid.UUID | None = None
    ) -> list[ProjectMemberOut]:
        await self.repository.get(project_id, scope)
        user_ids = await self.member_repository.list_user_ids(project_id)
        users = await self.identity_service.list_public_users(user_ids)
        return [
            ProjectMemberOut(id=user.id, display_name=user.display_name, email=user.email)
            for user in users
        ]

    async def add_member(
        self,
        project_id: uuid.UUID,
        user_id: uuid.UUID,
        scope: uuid.UUID | None = None,
    ) -> ProjectMemberOut:
        project = await self.repository.get(project_id, scope)
        # get_public_user raises NotFoundError(USER_NOT_FOUND) for a missing user.
        user = await self.identity_service.get_public_user(user_id)
        if user.organization_id != project.organization_id:
            raise NotFoundError(
                "Пользователь не найден в этой организации.",
                code="USER_NOT_FOUND",
            )
        await self.member_repository.add(project.id, user.id)
        return ProjectMemberOut(id=user.id, display_name=user.display_name, email=user.email)

    async def remove_member(
        self, project_id: uuid.UUID, user_id: uuid.UUID, scope: uuid.UUID | None = None
    ) -> None:
        await self.repository.get(project_id, scope)
        await self.member_repository.remove(project_id, user_id)