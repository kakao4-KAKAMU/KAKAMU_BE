from uuid import UUID

from pydantic import BaseModel


class Mention(BaseModel):
    id: UUID
    nickname: str
    tag: str
