import re
from pydantic import BaseModel, field_validator
from typing import Literal
from uuid import UUID

class MovieEvaluationRequest(BaseModel):
    persona_id: UUID
    movie_id: str
    evaluation: Literal["LIKE", "DISLIKE"]

    @field_validator("movie_id")
    @classmethod
    def validate_movie_id(cls, v: str) -> str:
        # UUID 형식 검사 (8-4-4-4-12)
        uuid_pattern = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")
        # 더미 영화 포맷 검사 ("movie" + 숫자)
        dummy_pattern = re.compile(r"^movie\d+$")
        
        if not uuid_pattern.match(v) and not dummy_pattern.match(v):
            raise ValueError("movie_id must be a valid UUID or match the 'movie[0-9]+' pattern.")
        return v
