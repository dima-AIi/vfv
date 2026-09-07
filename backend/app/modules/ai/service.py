import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.core.pagination import PageParams
from app.modules.ai.provider import AIRequest
from app.modules.ai.registry import get_provider
from app.modules.ai.repository import AIRepository
from app.modules.ai.schemas import (
    ACTION_TYPES,
    AIActionCreate,
    AIActionDetail,
)
from app.modules.documents.service import DocumentService
from app.modules.projects.service import ProjectService
from app.modules.tasks.service import TaskService

CONTEXT_TEXT_LIMIT = 8000


class AIService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self.repository = AIRepository(session)
        self.project_service = ProjectService(session)
        self.task_service = TaskService(session)

    async def run_action(
        self,
        data: AIActionCreate,
        organization_id: uuid.UUID | None = None,
    ) -> AIActionDetail:
        scope = organization_id

        if data.action_type not in ACTION_TYPES:
            raise AppError(
                f"Тип действия должен быть одним из: {', '.join(ACTION_TYPES)}.",
                code="INVALID_ACTION_TYPE",
                status_code=422,
            )

        project_name: str | None = None
        task_title: str | None = None
        context_summary_parts: list[str] = []
        context_sections: list[str] = []

        if data.project_id is not None:
            project = await self.project_service.get_model(data.project_id, scope)
            project_name = project.name
            context_summary_parts.append(f"project={project.name}")
            context_sections.append(
                f"## Project: {project.name}\n\n{project.description}",
            )

        if data.task_id is not None:
            task = await self.task_service.get_model(data.task_id, scope)
            task_title = task.title
            context_summary_parts.append(f"task={task.title}")
            context_sections.append(
                f"## Task: {task.title}\n\n{task.description} [status={task.status}]",
            )

        document_service = DocumentService(self._session)
        for document_id in data.document_ids:
            document = await document_service.get_document(document_id, scope)
            content = await document_service.get_document_content(document.id, scope)
            text = (content.content or "(file unavailable)")[:CONTEXT_TEXT_LIMIT]
            context_sections.append(
                f"## {document.title} ({document.relative_path})\n\n{text}",
            )
            context_summary_parts.append(f"doc={document.relative_path}")

        provider = get_provider()
        action = await self.repository.create_action(data, provider.name, organization_id)

        request = AIRequest(
            action_type=data.action_type,
            input_text=data.input_text,
            context_text="\n\n".join(context_sections)[:CONTEXT_TEXT_LIMIT],
            project_name=project_name,
            task_title=task_title,
        )

        try:
            handler = getattr(provider, data.action_type, None)
            if handler is None:
                raise AppError(
                    f"Провайдер не поддерживает тип действия: {data.action_type}",
                    code="UNSUPPORTED_ACTION",
                    status_code=400,
                )
            response = await handler(request)
        except AppError:
            await self.repository.fail_action(action, "неподдерживаемое или некорректное действие")
            raise
        except Exception as exc:
            await self.repository.fail_action(action, str(exc))
            raise AppError(
                "AI-действие завершилось ошибкой.",
                code="AI_ACTION_FAILED",
                status_code=500,
            ) from exc

        await self.repository.save_result(action.id, response.content, response.summary)
        completed = await self.repository.complete_action(
            action,
            "; ".join(context_summary_parts),
        )
        return await self.repository.get_detail(completed.id)

    async def get_action(
        self,
        action_id: uuid.UUID,
        scope: uuid.UUID | None = None,
    ) -> AIActionDetail:
        return await self.repository.get_detail(action_id, scope)

    async def list_actions(
        self,
        params: PageParams,
        project_id: uuid.UUID | None = None,
        scope: uuid.UUID | None = None,
    ) -> tuple[list[AIActionDetail], int]:
        actions, total = await self.repository.list_for_project(
            project_id,
            params,
            scope,
        )
        return [self.repository.to_detail(a) for a in actions], total

    async def count(self, scope: uuid.UUID | None = None) -> int:
        return await self.repository.count(scope)

    async def list_recent(
        self,
        limit: int = 5,
        scope: uuid.UUID | None = None,
    ) -> list[AIActionDetail]:
        actions = await self.repository.list_recent(limit, scope)
        return [self.repository.to_detail(a) for a in actions]
