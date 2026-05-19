from pydantic import BaseModel
from enum import Enum

class BlockLevel(str, Enum):
    PERSONA = "PERSONA"
    USER = "USER"

class RelationResponse(BaseModel):
    status: str
    message: str

class BlockRequest(BaseModel):
    level: BlockLevel = BlockLevel.PERSONA