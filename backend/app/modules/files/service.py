import hashlib
import uuid
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import AuditService
from app.core.config import get_settings
from app.core.errors import AppError
from app.core.pagination import PageParams
from app.modules.files.repository import FileRepository
from app.modules.files.schemas import FileOut, FileSearchResult, FileVersionOut
from app.modules.files.storage import LocalFileStorage, StorageError
from app.modules.identity.deps import OrgContext

AUDIT_ENTITY = "file"


class FileService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self.repository = FileRepository(session)
        self.audit = AuditService(session)
        self._storage = LocalFileStorage(get_settings().storage_dir)

    async def upload(
        self,
        *,
        data: bytes,
        filename: str,
        mime_type: str,
        context: OrgContext,
    ) -> FileOut:
        self._ensure_within_limit(data)
        checksum = hashlib.sha256(data).hexdigest()
        storage_key = self._storage.save(data, Path(filename).suffix)
        file = await self.repository.create(
            organization_id=context.organization_id,
            filename=filename[:255],
            mime_type=mime_type[:100],
            size_bytes=len(data),
            checksum=checksum,
            storage_key=storage_key,
            created_by=context.user.id,
        )
        await self.audit.record(
            action_type="FILE_UPLOADED",
            entity_type=AUDIT_ENTITY,
            entity_id=file.id,
            user_id=context.user.id,
            detail={"filename": file.filename, "version": file.current_version},
            organization_id=context.organization_id,
        )
        return FileOut.model_validate(file)

    async def add_version(
        self,
        file_id: uuid.UUID,
        *,
        data: bytes,
        filename: str,
        mime_type: str,
        context: OrgContext,
    ) -> FileOut:
        file = await self.repository.get(file_id, context.scope)
        self._ensure_within_limit(data)
        checksum = hashlib.sha256(data).hexdigest()
        storage_key = self._storage.save(data, Path(filename).suffix)
        updated = await self.repository.add_version(
            file,
            storage_key=storage_key,
            size_bytes=len(data),
            checksum=checksum,
            created_by=context.user.id,
        )
        await self.audit.record(
            action_type="FILE_VERSION_ADDED",
            entity_type=AUDIT_ENTITY,
            entity_id=updated.id,
            user_id=context.user.id,
            detail={"filename": updated.filename, "version": updated.current_version},
            organization_id=context.organization_id,
        )
        return FileOut.model_validate(updated)

    async def list_files(
        self,
        params: PageParams,
        scope: uuid.UUID | None = None,
    ) -> tuple[list[FileOut], int]:
        files, total = await self.repository.list_page(params, scope)
        return [FileOut.model_validate(f) for f in files], total

    async def get_file(self, file_id: uuid.UUID, scope: uuid.UUID | None = None) -> FileOut:
        file = await self.repository.get(file_id, scope)
        return FileOut.model_validate(file)

    async def get_content(
        self,
        file_id: uuid.UUID,
        scope: uuid.UUID | None = None,
    ) -> tuple[FileOut, bytes]:
        file = await self.repository.get(file_id, scope)
        try:
            data = self._storage.read(file.storage_key)
        except StorageError as exc:
            raise AppError(str(exc), code="FILE_CONTENT_MISSING", status_code=404) from exc
        return FileOut.model_validate(file), data

    async def list_versions(
        self,
        file_id: uuid.UUID,
        scope: uuid.UUID | None = None,
    ) -> list[FileVersionOut]:
        versions = await self.repository.list_versions(file_id, scope)
        return [FileVersionOut.model_validate(v) for v in versions]

    async def delete_file(self, file_id: uuid.UUID, scope: uuid.UUID | None = None) -> None:
        file = await self.repository.get(file_id, scope)
        await self.repository.soft_delete(file)

    async def search(
        self,
        term: str,
        limit: int,
        scope: uuid.UUID | None = None,
    ) -> list[FileSearchResult]:
        files = await self.repository.search(term, limit, scope)
        return [FileSearchResult.model_validate(f) for f in files]

    def _ensure_within_limit(self, data: bytes) -> None:
        limit = get_settings().file_max_bytes
        if len(data) > limit:
            raise AppError(
                "Файл превышает максимально допустимый размер.",
                code="FILE_TOO_LARGE",
                status_code=413,
            )
