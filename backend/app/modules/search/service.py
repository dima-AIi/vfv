import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.crm.service import CustomerService
from app.modules.documents.service import DocumentService
from app.modules.files.service import FileService
from app.modules.projects.service import ProjectService
from app.modules.search.schemas import SearchResults
from app.modules.tasks.service import TaskService

HITS_PER_TYPE = 10


class SearchService:
    def __init__(self, session: AsyncSession) -> None:
        self.project_service = ProjectService(session)
        self.task_service = TaskService(session)
        self.document_service = DocumentService(session)
        self.file_service = FileService(session)
        self.customer_service = CustomerService(session)

    async def search(self, term: str, scope: uuid.UUID | None) -> SearchResults:
        projects = await self.project_service.search(term, HITS_PER_TYPE, scope)
        tasks = await self.task_service.search(term, HITS_PER_TYPE, scope)
        documents = await self.document_service.search(term, HITS_PER_TYPE, scope)
        files = await self.file_service.search(term, HITS_PER_TYPE, scope)
        customers = await self.customer_service.search(term, HITS_PER_TYPE, scope)
        return SearchResults(
            projects=projects,
            tasks=tasks,
            documents=documents,
            files=files,
            customers=customers,
        )
