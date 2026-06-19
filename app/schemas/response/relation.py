from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel

from app.schemas.base.user import UserSimpleWithFollow


class RelationResponse(BaseModel):
    status: str
    message: str


class FollowListResponse(BaseModel):
    items: List[UserSimpleWithFollow]
    next_cursor: Optional[UUID] = None
    has_next: bool

__all__ = ["RelationResponse", "FollowListResponse"]
