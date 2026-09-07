import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.errors import AppError, ValidationError
from app.core.pagination import PageParams
from app.modules.documents.repository import DocumentRepository, FolderRepository
from app.modules.documents.schemas import (
    CatalogEntry,
    DocumentContent,
    DocumentCreate,
    DocumentOut,
    DocumentSearchResult,
    FolderCreate,
    FolderOut,
)
from app.modules.documents.store import DocumentPathError, LocalDocumentStore
from app.modules.files.service import FileService
from app.modules.identity.deps import OrgContext

TEXT_MARKERS = ("text/", "markdown")


class DocumentService:
    def __init__(self, session: AsyncSession) -> None:
        self._store = LocalDocumentStore(get_settings())
        self.repository = DocumentRepository(session)
        self.folder_repository = FolderRepository(session)
        self.file_service = FileService(session)

    async def create_document(
        self,
        data: DocumentCreate,
        context: OrgContext,
    ) -> DocumentOut:
        has_path = data.relative_path is not None
        has_file = data.file_id is not None
        if has_path == has_file:
            raise ValidationError(
                "Требуется ровно один источник содержимого: relative_path или file_id.",
                code="INVALID_DOCUMENT_SOURCE",
            )
        relative_path: str | None = None
        if has_path:
            assert data.relative_path is not None
            try:
                self._store.resolve(data.relative_path)
            except DocumentPathError as exc:
                raise ValidationError(str(exc), code="INVALID_DOCUMENT_PATH") from exc
            relative_path = data.relative_path
        else:
            assert data.file_id is not None
            await self.file_service.get_file(data.file_id, context.scope)
        if data.folder_id is not None:
            await self.folder_repository.get(data.folder_id, context.scope)
        document = await self.repository.create(data, context.organization_id, relative_path)
        return DocumentOut.model_validate(document)

    async def list_documents(
        self,
        params: PageParams,
        scope: uuid.UUID | None = None,
        project_id: uuid.UUID | None = None,
        folder_id: uuid.UUID | None = None,
    ) -> tuple[list[DocumentOut], int]:
        documents, total = await self.repository.list_documents(
            params=params,
            scope=scope,
            project_id=project_id,
            folder_id=folder_id,
        )
        return [DocumentOut.model_validate(d) for d in documents], total

    async def get_document_content(
        self,
        document_id: uuid.UUID,
        scope: uuid.UUID | None = None,
    ) -> DocumentContent:
        document = await self.repository.get(document_id, scope)
        document_out = DocumentOut.model_validate(document)
        if document.file_id is not None:
            file_out, data = await self.file_service.get_content(document.file_id, scope)
            if _is_text_mime(file_out.mime_type):
                text = data.decode("utf-8", errors="replace")
                return DocumentContent(
                    document=document_out,
                    content=text,
                    missing=False,
                    is_binary=False,
                    download_url=None,
                )
            return DocumentContent(
                document=document_out,
                content=None,
                missing=False,
                is_binary=True,
                download_url=f"/api/v1/files/{document.file_id}/content",
            )
        try:
            if document.relative_path is None:
                return DocumentContent(
                    document=document_out, content=None, missing=True,
                )
            resolved = self._store.resolve(document.relative_path)
            content = self._store.read(resolved)
            return DocumentContent(
                document=document_out, content=content, missing=False,
            )
        except DocumentPathError:
            return DocumentContent(
                document=document_out, content=None, missing=True,
            )

    async def get_document(
        self,
        document_id: uuid.UUID,
        scope: uuid.UUID | None = None,
    ) -> DocumentOut:
        document = await self.repository.get(document_id, scope)
        return DocumentOut.model_validate(document)

    async def count_documents(self, scope: uuid.UUID | None = None) -> int:
        return await self.repository.count(scope)

    async def count_for_project(
        self,
        project_id: uuid.UUID,
        scope: uuid.UUID | None = None,
    ) -> int:
        return await self.repository.count_for_project(project_id, scope)

    async def search(
        self,
        term: str,
        limit: int,
        scope: uuid.UUID | None = None,
    ) -> list[DocumentSearchResult]:
        documents = await self.repository.search(term, limit, scope)
        return [DocumentSearchResult.model_validate(d) for d in documents]

    async def delete_document(
        self,
        document_id: uuid.UUID,
        scope: uuid.UUID | None = None,
    ) -> None:
        await self.repository.soft_delete(document_id, scope)

    def catalog(self, params: PageParams) -> tuple[list[CatalogEntry], int]:
        entries = [CatalogEntry.model_validate(e) for e in self._store.catalog()]
        if not params.descending:
            entries = list(reversed(entries))
        total = len(entries)
        start = params.offset
        end = start + params.page_size
        return entries[start:end], total


class FolderService:
    def __init__(self, session: AsyncSession) -> None:
        self.repository = FolderRepository(session)
        self.document_repository = DocumentRepository(session)

    async def create_folder(
        self,
        data: FolderCreate,
        context: OrgContext,
    ) -> FolderOut:
        if data.parent_id is not None:
            await self.repository.get(data.parent_id, context.scope)
        folder = await self.repository.create(data, context.organization_id)
        return FolderOut.model_validate(folder)

    async def list_folders(
        self,
        params: PageParams,
        scope: uuid.UUID | None = None,
        parent_id: uuid.UUID | None = None,
    ) -> tuple[list[FolderOut], int]:
        folders, total = await self.repository.list_folders(params, scope, parent_id)
        return [FolderOut.model_validate(f) for f in folders], total

    async def delete_folder(self, folder_id: uuid.UUID, scope: uuid.UUID | None = None) -> None:
        folder = await self.repository.get(folder_id, scope)
        document_count = await self.document_repository.count_in_folder(folder.id)
        child_count = await self.repository.count_children(folder.id)
        if document_count > 0 or child_count > 0:
            raise AppError(
                "В папке есть активные документы или вложенные папки — удаление невозможно.",
                code="FOLDER_NOT_EMPTY",
                status_code=409,
                details=[{"documents": document_count, "folders": child_count}],
            )
        await self.repository.soft_delete(folder)


def _is_text_mime(mime_type: str) -> bool:
    lowered = mime_type.lower()
    return any(marker in lowered for marker in TEXT_MARKERS)
