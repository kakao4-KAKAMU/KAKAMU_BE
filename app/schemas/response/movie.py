from pydantic import BaseModel
from uuid import UUID
from app.schemas.response.common import SuccessResponse

class WatchMovieResponse(SuccessResponse):
    message: str

class MovieRecommendationResponse(BaseModel):
    recommendations: str
    for_persona: UUID
