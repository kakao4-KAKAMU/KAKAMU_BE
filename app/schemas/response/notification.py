from typing import List

from pydantic import BaseModel, Field

from app.schemas.base.notification import Notification

NotificationItem = Notification

__all__ = ["NotificationItem", "NotificationListResponse"]


class NotificationListResponse(BaseModel):
    items: List[NotificationItem]
    unread_count: int = Field(..., description="읽지 않은 새 알림 개수 (배지 표시용)")
