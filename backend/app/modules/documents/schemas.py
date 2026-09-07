import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DocumentCreate(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    relative_path: str | None = Field(default=None, min_length=1, max_length=1000)
    category: str = Field(default="general", max_length=50)
    project_id: uuid.UUID | None = None
    folder_id: uuid.UUID | None = None
    file_id: uuid.UUID | None = None


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID | None
    title: str
    category: str
    relative_path: str | None
    folder_id: uuid.UUID | None
    file_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime


class FolderCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    parent_id: uuid.UUID | None = None


class FolderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    parent_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime


class CatalogEntry(BaseModel):
    relative_path: str
    name: str
    root_name: str
    size_bytes: int


class DocumentContent(BaseModel):
    document: DocumentOut
    content: str | None
    missing: bool
    is_binary: bool = False
    download_url: str | None = None


class DocumentSearchResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    project_id: uuid.UUID | None
    folder_id: uuid.UUID | None
