from pydantic import BaseModel

from app.modules.crm.schemas import CustomerSearchResult
from app.modules.documents.schemas import DocumentSearchResult
from app.modules.files.schemas import FileSearchResult
from app.modules.projects.schemas import ProjectSearchResult
from app.modules.tasks.schemas import TaskSearchResult


class SearchResults(BaseModel):
    projects: list[ProjectSearchResult]
    tasks: list[TaskSearchResult]
    documents: list[DocumentSearchResult]
    files: list[FileSearchResult]
    customers: list[CustomerSearchResult]
