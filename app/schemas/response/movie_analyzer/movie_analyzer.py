from datetime import datetime
from typing import List, Literal, Optional
from uuid import UUID

from pydantic import BaseModel

from app.schemas.base.movie import MovieWithTrailers
from app.schemas.base.persona import Persona


class MovieEvaluationResponse(BaseModel):
    message: str
    user_id: UUID
    persona_id: Optional[UUID] = None
    movie_id: UUID
    evaluation: str


class MovieToEvaluateListResponse(BaseModel):
    items: List[MovieWithTrailers]


class MovieEvaluationItem(BaseModel):
    id: int
    evaluation: Literal["LIKE", "DISLIKE"]
    created_at: datetime
    persona: Optional[Persona] = None
    movie: MovieWithTrailers


class MovieEvaluationListResponse(BaseModel):
    items: List[MovieEvaluationItem]
    next_cursor: Optional[int] = None
    has_next: bool
