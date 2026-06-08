from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID

class RelationResponse(BaseModel):
    status: str
    message: str

class UserSimpleInfo(BaseModel):
    id: UUID
    nickname: str
    username: str

class FollowListResponse(BaseModel):
    items: List[UserSimpleInfo]
    next_cursor: Optional[UUID] = None
    has_next: bool
