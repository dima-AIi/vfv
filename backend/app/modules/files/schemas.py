import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class FileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID | None
    filename: str
    mime_type: str
    size_bytes: int
    checksum: str
    current_version: int
    status: str
    created_by: uuid.UUID | None
    created_at: datetime
    updated_at: datetime


class FileVersionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    file_id: uuid.UUID
    version: int
    size_bytes: int
    checksum: str
    created_by: uuid.UUID | None
    created_at: datetime


class FileSearchResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    filename: str
    mime_type: str
