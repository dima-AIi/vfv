import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

ACTION_TYPES = ("analyze", "plan", "execute", "summarize")
ACTION_STATUSES = ("pending", "completed", "failed")


class AIActionCreate(BaseModel):
    action_type: str
    input_text: str = Field(min_length=1, max_length=20000)
    project_id: uuid.UUID | None = None
    task_id: uuid.UUID | None = None
    document_ids: list[uuid.UUID] = Field(default_factory=list)


class AIResultOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    action_id: uuid.UUID
    content: str
    summary: str
    created_at: datetime


class AIActionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID | None
    task_id: uuid.UUID | None
    action_type: str
    input_text: str
    context_summary: str
    status: str
    provider: str
    error: str
    created_at: datetime
    completed_at: datetime | None


class AIActionDetail(AIActionOut):
    result: AIResultOut | None = None


class AIActionListOut(BaseModel):
    items: list[AIActionDetail]
    total: int
