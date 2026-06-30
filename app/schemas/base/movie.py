from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel

from app.schemas.base.genre import Genre
from app.schemas.base.person import Person
from app.schemas.base.youtube_video import YoutubeVideo


class Movie(BaseModel):
    id: UUID
    title: str
    poster_url: Optional[str] = None
    release_date: Optional[str] = None


class MovieWithTrailers(Movie):
    youtube_videos: List[YoutubeVideo] = []


class MovieTitle(BaseModel):
    title_name: str
    country: str
    is_original: bool


class Overview(BaseModel):
    platform: str
    lang: Optional[str] = None
    overview: str


class MovieDetail(BaseModel):
    id: UUID
    titles: List[MovieTitle]
    poster_url: Optional[str] = None
    nation: Optional[str] = None
    release_date: Optional[str] = None
    producing_year: Optional[int] = None
    runtime: Optional[int] = None
    is_adult: bool
    youtube_videos: List[YoutubeVideo] = []
    overviews: List[Overview] = []
    genres: List[Genre] = []
    staffs: List[Person] = []
