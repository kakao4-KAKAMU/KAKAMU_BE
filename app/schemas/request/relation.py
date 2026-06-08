from pydantic import BaseModel
from enum import Enum

class BlockLevel(str, Enum):
    PERSONA = "PERSONA"
    USER = "USER"

class BlockRequest(BaseModel):
    level: BlockLevel = BlockLevel.USER
