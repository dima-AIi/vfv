import uuid
from urllib.parse import quote

from fastapi import APIRouter, Depends, File, UploadFile, status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.envelope import Envelope, pagination_meta
from app.core.pagination import PageParams, get_page_params
from app.modules.files.schemas import FileOut, FileVersionOut
from app.modules.files.service import FileService
from app.modules.identity.deps import OrgContext, require_permission

router = APIRouter(prefix="/files", tags=["files"])

MAX_HEADER_FILENAME = 200
DEFAULT_DOWNLOAD_NAME = "file"


def get_service(session: AsyncSession = Depends(get_session)) -> FileService:
    return FileService(session)


def _strip_control(name: str) -> str:
    return "".join(char for char in name if ord(char) >= 32 and ord(char) != 127)


def _ascii_fallback(name: str) -> str:
    ascii_only = "".join(
        char if 32 <= ord(char) <= 126 and char not in {'"', "\\"} else "_"
        for char in name
    )
    cleaned = ascii_only.strip()[:MAX_HEADER_FILENAME]
    return cleaned or DEFAULT_DOWNLOAD_NAME


def _content_disposition(name: str) -> str:
    fallback = _ascii_fallback(name)
    encoded = quote(_strip_control(name), safe="")
    return f"attachment; filename=\"{fallback}\"; filename*=UTF-8''{encoded}"


@router.post("", status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = File(...),
    context: OrgContext = Depends(require_permission("files.file.upload")),
    service: FileService = Depends(get_service),
) -> Envelope[FileOut]:
    data = await file.read()
    file_out = await service.upload(
        data=data,
        filename=file.filename or DEFAULT_DOWNLOAD_NAME,
        mime_type=file.content_type or "",
        context=context,
    )
    return Envelope(data=file_out)


@router.get("")
async def list_files(
    params: PageParams = Depends(get_page_params),
    context: OrgContext = Depends(require_permission("files.file.read")),
    service: FileService = Depends(get_service),
) -> Envelope[list[FileOut]]:
    files, total = await service.list_files(params, context.scope)
    return Envelope(
        data=files,
        meta=pagination_meta(
            page=params.page,
            page_size=params.page_size,
            total_items=total,
        ),
    )


@router.get("/{file_id}")
async def get_file(
    file_id: uuid.UUID,
    context: OrgContext = Depends(require_permission("files.file.read")),
    service: FileService = Depends(get_service),
) -> Envelope[FileOut]:
    return Envelope(data=await service.get_file(file_id, context.scope))


@router.get("/{file_id}/content")
async def download_file(
    file_id: uuid.UUID,
    context: OrgContext = Depends(require_permission("files.file.read")),
    service: FileService = Depends(get_service),
) -> Response:
    file_out, data = await service.get_content(file_id, context.scope)
    media_type = file_out.mime_type or "application/octet-stream"
    return Response(
        content=data,
        media_type=media_type,
        headers={"Content-Disposition": _content_disposition(file_out.filename)},
    )


@router.post("/{file_id}/versions", status_code=status.HTTP_201_CREATED)
async def add_version(
    file_id: uuid.UUID,
    file: UploadFile = File(...),
    context: OrgContext = Depends(require_permission("files.file.upload")),
    service: FileService = Depends(get_service),
) -> Envelope[FileOut]:
    data = await file.read()
    file_out = await service.add_version(
        file_id,
        data=data,
        filename=file.filename or DEFAULT_DOWNLOAD_NAME,
        mime_type=file.content_type or "",
        context=context,
    )
    return Envelope(data=file_out)


@router.get("/{file_id}/versions")
async def list_versions(
    file_id: uuid.UUID,
    context: OrgContext = Depends(require_permission("files.file.read")),
    service: FileService = Depends(get_service),
) -> Envelope[list[FileVersionOut]]:
    versions = await service.list_versions(file_id, context.scope)
    return Envelope(data=versions)


@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(
    file_id: uuid.UUID,
    context: OrgContext = Depends(require_permission("files.file.delete")),
    service: FileService = Depends(get_service),
) -> None:
    await service.delete_file(file_id, context.scope)
