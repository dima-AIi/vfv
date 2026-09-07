import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.envelope import Envelope, pagination_meta
from app.core.pagination import PageParams, get_page_params
from app.modules.documents.schemas import (
    CatalogEntry,
    DocumentContent,
    DocumentCreate,
    DocumentOut,
    FolderCreate,
    FolderOut,
)
from app.modules.documents.service import DocumentService, FolderService
from app.modules.identity.deps import OrgContext, require_permission

router = APIRouter(prefix="/documents", tags=["documents"])


def get_service(session: AsyncSession = Depends(get_session)) -> DocumentService:
    return DocumentService(session)


def get_folder_service(session: AsyncSession = Depends(get_session)) -> FolderService:
    return FolderService(session)


@router.get("/catalog")
async def catalog(
    params: PageParams = Depends(get_page_params),
    context: OrgContext = Depends(require_permission("documents.document.read")),
    service: DocumentService = Depends(get_service),
) -> Envelope[list[CatalogEntry]]:
    entries, total = service.catalog(params)
    return Envelope(
        data=entries,
        meta=pagination_meta(
            page=params.page,
            page_size=params.page_size,
            total_items=total,
        ),
    )


@router.post("/folders", status_code=status.HTTP_201_CREATED)
async def create_folder(
    data: FolderCreate,
    context: OrgContext = Depends(require_permission("documents.document.create")),
    service: FolderService = Depends(get_folder_service),
) -> Envelope[FolderOut]:
    return Envelope(data=await service.create_folder(data, context))


@router.get("/folders")
async def list_folders(
    params: PageParams = Depends(get_page_params),
    parent_id: uuid.UUID | None = None,
    context: OrgContext = Depends(require_permission("documents.document.read")),
    service: FolderService = Depends(get_folder_service),
) -> Envelope[list[FolderOut]]:
    folders, total = await service.list_folders(params, context.scope, parent_id)
    return Envelope(
        data=folders,
        meta=pagination_meta(
            page=params.page,
            page_size=params.page_size,
            total_items=total,
        ),
    )


@router.delete("/folders/{folder_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_folder(
    folder_id: uuid.UUID,
    context: OrgContext = Depends(require_permission("documents.document.delete")),
    service: FolderService = Depends(get_folder_service),
) -> None:
    await service.delete_folder(folder_id, context.scope)


@router.get("")
async def list_documents(
    params: PageParams = Depends(get_page_params),
    project_id: uuid.UUID | None = None,
    folder_id: uuid.UUID | None = None,
    context: OrgContext = Depends(require_permission("documents.document.read")),
    service: DocumentService = Depends(get_service),
) -> Envelope[list[DocumentOut]]:
    documents, total = await service.list_documents(
        params=params,
        scope=context.scope,
        project_id=project_id,
        folder_id=folder_id,
    )
    return Envelope(
        data=documents,
        meta=pagination_meta(
            page=params.page,
            page_size=params.page_size,
            total_items=total,
        ),
    )


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_document(
    data: DocumentCreate,
    context: OrgContext = Depends(require_permission("documents.document.create")),
    service: DocumentService = Depends(get_service),
) -> Envelope[DocumentOut]:
    return Envelope(data=await service.create_document(data, context))


@router.get("/{document_id}")
async def get_document_content(
    document_id: uuid.UUID,
    context: OrgContext = Depends(require_permission("documents.document.read")),
    service: DocumentService = Depends(get_service),
) -> Envelope[DocumentContent]:
    return Envelope(data=await service.get_document_content(document_id, context.scope))


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: uuid.UUID,
    context: OrgContext = Depends(require_permission("documents.document.delete")),
    service: DocumentService = Depends(get_service),
) -> None:
    await service.delete_document(document_id, context.scope)
