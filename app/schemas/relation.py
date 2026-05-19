from pydantic import BaseModel
from enum import Enum
from typing import List, Optional

class BlockLevel(str, Enum):
    PERSONA = "PERSONA"
    USER = "USER"

class RelationResponse(BaseModel):
    status: str
    message: str

class BlockRequest(BaseModel):
    level: BlockLevel = BlockLevel.PERSONA

class PersonaSimpleInfo(BaseModel):
    id: int
    nickname: str
    tag: str
    profile_image_url: Optional[str] = None

class FollowListResponse(BaseModel):
    items: List[PersonaSimpleInfo]
    next_cursor: Optional[int] = None
    has_next: bool