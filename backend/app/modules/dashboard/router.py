from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.envelope import Envelope
from app.modules.ai.schemas import AIActionDetail
from app.modules.ai.service import AIService
from app.modules.documents.service import DocumentService
from app.modules.identity.deps import OrgContext, require_permission
from app.modules.projects.schemas import ProjectOut
from app.modules.projects.service import ProjectService
from app.modules.tasks.service import TaskService

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


class DashboardStats(BaseModel):
    projects: int
    tasks: int
    documents: int
    ai_actions: int


class DashboardOut(BaseModel):
    stats: DashboardStats
    recent_projects: list[ProjectOut]
    recent_ai_actions: list[AIActionDetail]


@router.get("")
async def dashboard(
    context: OrgContext = Depends(require_permission("dashboard.dashboard.read")),
    session: AsyncSession = Depends(get_session),
) -> Envelope[DashboardOut]:
    project_service = ProjectService(session)
    task_service = TaskService(session)
    document_service = DocumentService(session)
    ai_service = AIService(session)

    scope = context.scope

    return Envelope(
        data=DashboardOut(
            stats=DashboardStats(
                projects=await project_service.count(scope),
                tasks=await task_service.count(scope),
                documents=await document_service.count_documents(scope),
                ai_actions=await ai_service.count(scope),
            ),
            recent_projects=await project_service.list_recent(5, scope),
            recent_ai_actions=await ai_service.list_recent(5, scope),
        ),
    )
