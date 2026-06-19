from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class Movie(BaseModel):
    id: UUID
    title: str
    poster_url: Optional[str] = None
    release_date: Optional[str] = None
