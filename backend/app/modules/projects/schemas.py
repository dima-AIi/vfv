import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=5000)
    due_date: date | None = None


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    status: str | None = None
    customer_id: uuid.UUID | None = None
    due_date: date | None = None


class ProjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: str
    status: str
    due_date: date | None
    customer_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime


class ProjectMemberOut(BaseModel):
    id: uuid.UUID
    display_name: str
    email: str


class ProjectMemberAdd(BaseModel):
    user_id: uuid.UUID = Field(alias="userId")

    model_config = ConfigDict(populate_by_name=True)


class ProjectSearchResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    status: str
