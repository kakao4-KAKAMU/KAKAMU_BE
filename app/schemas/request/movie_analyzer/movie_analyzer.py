import re
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, field_validator


class MovieEvaluationRequest(BaseModel):
    movie_id: UUID
    evaluation: Literal["LIKE", "DISLIKE"]
    persona_id: Optional[UUID] = None

    @field_validator("movie_id", mode="before")
    @classmethod
    def validate_movie_id(cls, v: object) -> object:
        if isinstance(v, UUID):
            return v
        if isinstance(v, str):
            uuid_pattern = re.compile(
                r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
            )
            if not uuid_pattern.match(v):
                raise ValueError("movie_id must be a valid UUID.")
        return v
