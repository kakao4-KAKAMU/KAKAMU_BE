from typing import List
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import FavGenre, FavMovie, FavPeople, Persona
from app.models.movie import Movie
from app.schemas.base.persona import Persona as PersonaSchema
from app.schemas.mapper.persona import PersonaMapper


class PersonaReadService:
    @staticmethod
    def _persona_load_options():
        return (
            selectinload(Persona.fav_genres).selectinload(FavGenre.genre),
            selectinload(Persona.fav_people).selectinload(FavPeople.person),
            selectinload(Persona.fav_movies).selectinload(FavMovie.movie).selectinload(Movie.titles),
        )

    @staticmethod
    async def get_my_personas(db: Session, user_id: UUID) -> List[PersonaSchema]:
        stmt = (
            select(Persona)
            .where(
                Persona.user_id == user_id,
                Persona.status != "DELETED",
            )
            .options(*PersonaReadService._persona_load_options())
        )

        personas = list(db.scalars(stmt).all())
        return [PersonaMapper.to_persona(persona) for persona in personas]

    @staticmethod
    async def get_persona_detail(
        db: Session,
        user_id: UUID,
        persona_id: UUID
    ) -> PersonaSchema:
        stmt = (
            select(Persona)
            .where(
                Persona.id == persona_id,
                Persona.user_id == user_id,
                Persona.status != "DELETED",
            )
            .options(*PersonaReadService._persona_load_options())
        )

        persona = db.scalar(stmt)

        if not persona:
            raise HTTPException(
                status_code=404,
                detail={"code": "PERSONA_NOT_FOUND", "message": "페르소나를 찾을 수 없습니다."}
            )

        return PersonaMapper.to_persona(persona)
