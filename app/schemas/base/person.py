from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class Person(BaseModel):
    id: UUID
    name: str
    job: Optional[str] = None
    profile_image: Optional[str] = None
