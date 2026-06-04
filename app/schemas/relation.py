from pydantic import BaseModel
from enum import Enum
from typing import List, Optional
from uuid import UUID

class BlockLevel(str, Enum):
    PERSONA = "PERSONA"
    USER = "USER"

class RelationResponse(BaseModel):
    status: str
    message: str

class BlockRequest(BaseModel):
    level: BlockLevel = BlockLevel.USER

class UserSimpleInfo(BaseModel):
    id: UUID
    nickname: str
    username: str

class FollowListResponse(BaseModel):
    items: List[UserSimpleInfo]
    next_cursor: Optional[UUID] = None
    has_next: bool