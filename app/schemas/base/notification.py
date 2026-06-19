from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class Notification(BaseModel):
    id: int
    receiver_user_id: UUID
    sender_persona_id: Optional[UUID]
    sender_nickname: Optional[str]
    type: str
    target_type: str
    target_id: str
    message: str
    is_read: bool
    created_at: datetime
