from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class Persona(BaseModel):
    id: UUID
    user_id: UUID
    nickname: str
    profile_image_url: Optional[str] = None
