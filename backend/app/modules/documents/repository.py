import uuid

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError
from app.core.models import utcnow
from app.core.pagination import PageParams
from app.modules.documents.models import Document, Folder
from app.modules.documents.schemas import DocumentCreate, FolderCreate


class DocumentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        data: DocumentCreate,
        organization_id: uuid.UUID | None,
        relative_path: str | None,
    ) -> Document:
        document = Document(
            title=data.title,
            category=data.category,
            relative_path=relative_path,
            project_id=data.project_id,
            folder_id=data.folder_id,
            file_id=data.file_id,
            organization_id=organization_id,
        )
        self._session.add(document)
        await self._session.commit()
        await self._session.refresh(document)
        return document

    async def get(
        self,
        document_id: uuid.UUID,
        scope: uuid.UUID | None = None,
    ) -> Document:
        query = select(Document).where(
            Document.id == document_id,
            Document.deleted_at.is_(None),
        )
        if scope is not None:
            query = query.where(Document.organization_id == scope)
        result = await self._session.execute(query)
        document = result.scalar_one_or_none()
        if document is None:
            raise NotFoundError(
                "Документ не найден.",
                code="DOCUMENT_NOT_FOUND",
            )
        return document

    async def list_documents(
        self,
        params: PageParams,
        scope: uuid.UUID | None = None,
        project_id: uuid.UUID | None = None,
        folder_id: uuid.UUID | None = None,
    ) -> tuple[list[Document], int]:
        active = Document.deleted_at.is_(None)
        order = Document.created_at.desc() if params.descending else Document.created_at.asc()
        query: Select[tuple[Document]] = select(Document).where(active).order_by(order)
        count_query: Select[tuple[int]] = (
            select(func.count()).select_from(Document).where(active)
        )
        if scope is not None:
            query = query.where(Document.organization_id == scope)
            count_query = count_query.where(Document.organization_id == scope)
        if project_id is not None:
            query = query.where(Document.project_id == project_id)
            count_query = count_query.where(Document.project_id == project_id)
        if folder_id is not None:
            query = query.where(Document.folder_id == folder_id)
            count_query = count_query.where(Document.folder_id == folder_id)
        query = query.limit(params.page_size).offset(params.offset)
        items_result = await self._session.execute(query)
        total_result = await self._session.execute(count_query)
        return list(items_result.scalars().all()), int(total_result.scalar_one())

    async def count(self, scope: uuid.UUID | None = None) -> int:
        query = (
            select(func.count())
            .select_from(Document)
            .where(Document.deleted_at.is_(None))
        )
        if scope is not None:
            query = query.where(Document.organization_id == scope)
        result = await self._session.execute(query)
        return int(result.scalar_one())

    async def count_for_project(
        self,
        project_id: uuid.UUID,
        scope: uuid.UUID | None = None,
    ) -> int:
        query = (
            select(func.count())
            .select_from(Document)
            .where(Document.project_id == project_id, Document.deleted_at.is_(None))
        )
        if scope is not None:
            query = query.where(Document.organization_id == scope)
        result = await self._session.execute(query)
        return int(result.scalar_one())

    async def count_in_folder(self, folder_id: uuid.UUID) -> int:
        query = (
            select(func.count())
            .select_from(Document)
            .where(
                Document.folder_id == folder_id,
                Document.deleted_at.is_(None),
            )
        )
        result = await self._session.execute(query)
        return int(result.scalar_one())

    async def soft_delete(self, document_id: uuid.UUID, scope: uuid.UUID | None = None) -> None:
        document = await self.get(document_id, scope)
        document.deleted_at = utcnow()
        await self._session.commit()

    async def search(
        self,
        term: str,
        limit: int,
        scope: uuid.UUID | None = None,
    ) -> list[Document]:
        from app.core.search import LIKE_ESCAPE, like_contains

        pattern = like_contains(term)
        query = (
            select(Document)
            .where(
                Document.deleted_at.is_(None),
                func.lower(Document.title).like(pattern, escape=LIKE_ESCAPE),
            )
            .order_by(Document.created_at.desc())
            .limit(limit)
        )
        if scope is not None:
            query = query.where(Document.organization_id == scope)
        result = await self._session.execute(query)
        return list(result.scalars().all())


class FolderRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        data: FolderCreate,
        organization_id: uuid.UUID | None,
    ) -> Folder:
        folder = Folder(
            name=data.name,
            parent_id=data.parent_id,
            organization_id=organization_id,
        )
        self._session.add(folder)
        await self._session.commit()
        await self._session.refresh(folder)
        return folder

    async def get(self, folder_id: uuid.UUID, scope: uuid.UUID | None = None) -> Folder:
        query = select(Folder).where(Folder.id == folder_id, Folder.deleted_at.is_(None))
        if scope is not None:
            query = query.where(Folder.organization_id == scope)
        result = await self._session.execute(query)
        folder = result.scalar_one_or_none()
        if folder is None:
            raise NotFoundError("Папка не найдена.", code="FOLDER_NOT_FOUND")
        return folder

    async def list_folders(
        self,
        params: PageParams,
        scope: uuid.UUID | None = None,
        parent_id: uuid.UUID | None = None,
    ) -> tuple[list[Folder], int]:
        active = Folder.deleted_at.is_(None)
        order = Folder.created_at.desc() if params.descending else Folder.created_at.asc()
        query: Select[tuple[Folder]] = select(Folder).where(active).order_by(order)
        count_query: Select[tuple[int]] = (
            select(func.count()).select_from(Folder).where(active)
        )
        if scope is not None:
            query = query.where(Folder.organization_id == scope)
            count_query = count_query.where(Folder.organization_id == scope)
        if parent_id is not None:
            query = query.where(Folder.parent_id == parent_id)
            count_query = count_query.where(Folder.parent_id == parent_id)
        query = query.limit(params.page_size).offset(params.offset)
        items_result = await self._session.execute(query)
        total_result = await self._session.execute(count_query)
        return list(items_result.scalars().all()), int(total_result.scalar_one())

    async def count_children(self, folder_id: uuid.UUID) -> int:
        query = (
            select(func.count())
            .select_from(Folder)
            .where(Folder.parent_id == folder_id, Folder.deleted_at.is_(None))
        )
        result = await self._session.execute(query)
        return int(result.scalar_one())

    async def soft_delete(self, folder: Folder) -> None:
        folder.deleted_at = utcnow()
        await self._session.commit()
