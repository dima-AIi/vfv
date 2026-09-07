import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel


class AuditRecordOut(BaseModel):
    id: uuid.UUID
    action_type: str
    entity_type: str
    entity_id: uuid.UUID | None
    user_id: uuid.UUID | None
    organization_id: uuid.UUID | None
    detail: dict[str, Any]
    created_at: datetime
