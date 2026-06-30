from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel

from app.schemas.base.genre import Genre
from app.schemas.base.movie import Movie
from app.schemas.base.person import Person


class Persona(BaseModel):
    id: UUID
    user_id: UUID
    nickname: str
    profile_image_url: Optional[str] = None
    fav_genres: List[Genre] = []
    fav_people: List[Person] = []
    fav_movies: List[Movie] = []
