import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    body: str
    entity_type: str
    entity_id: uuid.UUID | None
    read_at: datetime | None
    created_at: datetime
