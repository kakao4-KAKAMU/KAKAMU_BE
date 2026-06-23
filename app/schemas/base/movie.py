from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel

from app.schemas.base.youtube_video import YoutubeVideo


class Movie(BaseModel):
    id: UUID
    title: str
    poster_url: Optional[str] = None
    release_date: Optional[str] = None


class MovieWithTrailers(Movie):
    youtube_videos: List[YoutubeVideo] = []
