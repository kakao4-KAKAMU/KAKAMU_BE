from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional
from uuid import UUID

class NotificationItem(BaseModel):
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

    class Config:
        from_attributes = True

class NotificationListResponse(BaseModel):
    items: List[NotificationItem]
    unread_count: int = Field(..., description="읽지 않은 새 알림 개수 (배지 표시용)")