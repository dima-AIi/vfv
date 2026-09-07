import uuid

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError
from app.core.models import utcnow
from app.core.pagination import PageParams
from app.modules.files.models import File, FileVersion


class FileRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        organization_id: uuid.UUID | None,
        filename: str,
        mime_type: str,
        size_bytes: int,
        checksum: str,
        storage_key: str,
        created_by: uuid.UUID | None,
    ) -> File:
        file = File(
            organization_id=organization_id,
            filename=filename,
            mime_type=mime_type,
            size_bytes=size_bytes,
            checksum=checksum,
            storage_key=storage_key,
            current_version=1,
            status="active",
            created_by=created_by,
        )
        self._session.add(file)
        await self._session.flush()
        version = FileVersion(
            file_id=file.id,
            version=1,
            storage_key=storage_key,
            size_bytes=size_bytes,
            checksum=checksum,
            created_by=created_by,
        )
        self._session.add(version)
        await self._session.commit()
        await self._session.refresh(file)
        return file

    async def get(self, file_id: uuid.UUID, scope: uuid.UUID | None = None) -> File:
        query = select(File).where(File.id == file_id, File.deleted_at.is_(None))
        if scope is not None:
            query = query.where(File.organization_id == scope)
        result = await self._session.execute(query)
        file = result.scalar_one_or_none()
        if file is None:
            raise NotFoundError("Файл не найден.", code="FILE_NOT_FOUND")
        return file

    async def list_page(
        self,
        params: PageParams,
        scope: uuid.UUID | None = None,
    ) -> tuple[list[File], int]:
        active = File.deleted_at.is_(None)
        order = File.created_at.desc() if params.descending else File.created_at.asc()
        query: Select[tuple[File]] = (
            select(File).where(active).order_by(order).limit(params.page_size).offset(params.offset)
        )
        count_query: Select[tuple[int]] = (
            select(func.count()).select_from(File).where(active)
        )
        if scope is not None:
            query = query.where(File.organization_id == scope)
            count_query = count_query.where(File.organization_id == scope)
        items_result = await self._session.execute(query)
        total_result = await self._session.execute(count_query)
        return list(items_result.scalars().all()), int(total_result.scalar_one())

    async def add_version(
        self,
        file: File,
        *,
        storage_key: str,
        size_bytes: int,
        checksum: str,
        created_by: uuid.UUID | None,
    ) -> File:
        next_version = file.current_version + 1
        version = FileVersion(
            file_id=file.id,
            version=next_version,
            storage_key=storage_key,
            size_bytes=size_bytes,
            checksum=checksum,
            created_by=created_by,
        )
        self._session.add(version)
        file.current_version = next_version
        file.storage_key = storage_key
        file.size_bytes = size_bytes
        file.checksum = checksum
        await self._session.commit()
        await self._session.refresh(file)
        return file

    async def list_versions(
        self,
        file_id: uuid.UUID,
        scope: uuid.UUID | None = None,
    ) -> list[FileVersion]:
        await self.get(file_id, scope)
        result = await self._session.execute(
            select(FileVersion)
            .where(FileVersion.file_id == file_id)
            .order_by(FileVersion.version.asc()),
        )
        return list(result.scalars().all())

    async def soft_delete(self, file: File) -> None:
        file.deleted_at = utcnow()
        await self._session.commit()

    async def search(
        self,
        term: str,
        limit: int,
        scope: uuid.UUID | None = None,
    ) -> list[File]:
        from app.core.search import LIKE_ESCAPE, like_contains

        pattern = like_contains(term)
        query = (
            select(File)
            .where(
                File.deleted_at.is_(None),
                func.lower(File.filename).like(pattern, escape=LIKE_ESCAPE),
            )
            .order_by(File.created_at.desc())
            .limit(limit)
        )
        if scope is not None:
            query = query.where(File.organization_id == scope)
        result = await self._session.execute(query)
        return list(result.scalars().all())
