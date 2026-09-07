import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.modules.identity.schemas import UserOut


class OrganizationCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)


class InviteUserIn(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    display_name: str = Field(min_length=1, max_length=200, alias="displayName")
    password: str | None = Field(default=None, min_length=1, max_length=128)

    model_config = ConfigDict(populate_by_name=True)


class AssignRoleIn(BaseModel):
    role: str = Field(min_length=1, max_length=50)


class UserStatusIn(BaseModel):
    status: str = Field(min_length=1, max_length=20)


class OrganizationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: str | None
    status: str
    created_by: uuid.UUID | None
    version: int
    created_at: datetime
    updated_at: datetime


class InvitedUserOut(BaseModel):
    id: uuid.UUID
    email: str
    display_name: str
    organization_id: uuid.UUID
    generated_password: str | None = None


class MemberOut(BaseModel):
    id: uuid.UUID
    display_name: str


class OrganizationMemberOut(UserOut):
    roles: list[str] = Field(default_factory=list)
