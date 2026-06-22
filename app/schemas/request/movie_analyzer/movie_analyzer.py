from pydantic import BaseModel
from typing import Literal

class MovieEvaluationRequest(BaseModel):
    persona_id: str
    movie_id: str
    evaluation: Literal["LIKE", "DISLIKE"]
