from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.schemas.base.user import UserSimple


class CommentItem(BaseModel):
    id: int
    parent_id: Optional[int] = None
    user: UserSimple
    content: str
    is_spoiler: bool
    created_at: datetime
    like_count: int
    is_liked: bool

