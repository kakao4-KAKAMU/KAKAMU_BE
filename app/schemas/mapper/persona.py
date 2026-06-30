from typing import Optional

from app.core.config import settings
from app.models import Persona as PersonaModel
from app.schemas.base.persona import Persona
from app.schemas.mapper.genre import GenreMapper
from app.schemas.mapper.movie import MovieMapper
from app.schemas.mapper.person import PersonMapper


class PersonaMapper:
    @staticmethod
    def _resolve_profile_image_url(value: Optional[str]) -> Optional[str]:
        if not value:
            return value
        if value.startswith("http://") or value.startswith("https://"):
            return value
        if value.startswith("/static"):
            return f"{settings.DEFAULT_IMAGE.rstrip('/')}/{value.lstrip('/')}"
        return f"{settings.IMAGE_SERVER_URL.rstrip('/')}/{value.lstrip('/')}"

    @staticmethod
    def to_persona(persona: PersonaModel) -> Persona:
        return Persona(
            id=persona.id,
            user_id=persona.user_id,
            nickname=persona.nickname,
            profile_image_url=PersonaMapper._resolve_profile_image_url(persona.profile_image_url),
            fav_genres=[
                GenreMapper.to_genre(fav.genre)
                for fav in (persona.fav_genres or [])
                if fav.genre
            ],
            fav_people=[
                PersonMapper.to_person(fav.person, job=fav.type)
                for fav in (persona.fav_people or [])
                if fav.person
            ],
            fav_movies=[
                MovieMapper.to_movie(fav.movie)
                for fav in (persona.fav_movies or [])
                if fav.movie
            ],
        )
