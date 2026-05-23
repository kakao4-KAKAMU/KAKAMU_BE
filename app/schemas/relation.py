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
    level: BlockLevel = BlockLevel.PERSONA

class PersonaSimpleInfo(BaseModel):
    id: UUID
    nickname: str
    tag: str
    profile_image_url: Optional[str] = None

class FollowListResponse(BaseModel):
    items: List[PersonaSimpleInfo]
    next_cursor: Optional[UUID] = None
    has_next: bool