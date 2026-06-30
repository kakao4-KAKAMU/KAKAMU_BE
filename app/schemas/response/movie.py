from uuid import UUID

from pydantic import BaseModel

from app.schemas.base.common import SuccessResponse
from app.schemas.base.movie import MovieDetail

__all__ = ["WatchMovieResponse", "MovieRecommendationResponse", "MovieDetailResponse"]


class WatchMovieResponse(SuccessResponse):
    message: str


class MovieRecommendationResponse(BaseModel):
    recommendations: str
    for_persona: UUID


MovieDetailResponse = MovieDetail
