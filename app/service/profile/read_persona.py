from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models import Persona
from typing import List
from uuid import UUID

from app.schemas.base.persona import Persona as PersonaSchema
from app.schemas.mapper.persona import PersonaMapper


class PersonaReadService:

    @staticmethod
    async def get_my_personas(db: Session, user_id: UUID) -> List[PersonaSchema]:
        stmt = select(Persona).where(
            Persona.user_id == user_id,
            Persona.status != "DELETED"
        )

        personas = list(db.scalars(stmt).all())
        return [PersonaMapper.to_persona(persona) for persona in personas]

    @staticmethod
    async def get_persona_detail(
        db: Session,
        user_id: UUID,
        persona_id: UUID
    ) -> PersonaSchema:
        stmt = select(Persona).where(
            Persona.id == persona_id,
            Persona.user_id == user_id,
            Persona.status != "DELETED"
        )

        persona = db.scalar(stmt)

        if not persona:
            raise HTTPException(
                status_code=404,
                detail={"code": "PERSONA_NOT_FOUND", "message": "페르소나를 찾을 수 없습니다."}
            )

        return PersonaMapper.to_persona(persona)
