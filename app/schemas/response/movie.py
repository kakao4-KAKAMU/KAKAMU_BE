from uuid import UUID

from pydantic import BaseModel

from app.schemas.base.common import SuccessResponse

__all__ = ["WatchMovieResponse", "MovieRecommendationResponse"]


class WatchMovieResponse(SuccessResponse):
    message: str


class MovieRecommendationResponse(BaseModel):
    recommendations: str
    for_persona: UUID
