from uuid import UUID
from pydantic import BaseModel
from typing import Optional

class MovieEvaluationResponse(BaseModel):
    message: str
    persona_id: UUID
    movie_id: str
    evaluation: str

class UnratedTrailerResponse(BaseModel):
    movie_id: Optional[str] = None
    title: Optional[str] = None
    trailer_url: Optional[str] = None
    message: Optional[str] = None
