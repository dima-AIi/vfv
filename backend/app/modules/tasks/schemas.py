import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.modules.comments.schemas import CommentOut

TASK_STATUSES = ("open", "in_progress", "done")
TASK_PRIORITIES = ("low", "medium", "high")


class TaskCreate(BaseModel):
    project_id: uuid.UUID
    title: str = Field(min_length=1, max_length=300)
    description: str = Field(default="", max_length=5000)
    status: str = "open"
    priority: str = "medium"
    due_date: date | None = None
    assignee_id: uuid.UUID | None = None


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=300)
    description: str | None = Field(default=None, max_length=5000)
    status: str | None = None
    priority: str | None = None
    due_date: date | None = None
    assignee_id: uuid.UUID | None = None


class TaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    title: str
    description: str
    status: str
    priority: str
    due_date: date | None
    assignee_id: uuid.UUID | None
    assignee_name: str | None = None
    created_at: datetime
    updated_at: datetime


class TaskAttachmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    file_id: uuid.UUID
    filename: str
    mime_type: str
    size_bytes: int
    created_at: datetime
    created_by_name: str | None = None


class TaskAttachmentAdd(BaseModel):
    file_id: uuid.UUID = Field(alias="fileId")

    model_config = ConfigDict(populate_by_name=True)


class TaskDetail(TaskOut):
    comments: list[CommentOut] = Field(default_factory=list)
    attachments: list[TaskAttachmentOut] = Field(default_factory=list)


class TaskSearchResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    status: str
    project_id: uuid.UUID
