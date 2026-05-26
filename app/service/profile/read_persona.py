import re
from fastapi import HTTPException, status
from sqlalchemy import select, and_, func, update
from sqlalchemy.orm import Session
from app.models import Persona
from app.schemas.profile import PersonaCreate
from typing import List, Optional
from uuid import UUID

class PersonaReadService:

    # 내 모든 페르소나 조회
    @staticmethod
    async def get_my_personas(db: Session, user_id: UUID) -> List[Persona]:
        stmt = select(Persona).where(
            Persona.user_id == user_id,
            Persona.status != "DELETED"
        )

        return list(db.scalars(stmt).all())

    # 특정 페르소나 조회
    @staticmethod
    async def get_persona_detail(
        db: Session,
        user_id: UUID,
        persona_id: UUID
    ) -> Persona:
        stmt = select(Persona).where(
            Persona.id == persona_id,
            Persona.user_id == user_id,
            Persona.status != "DELETED"
        )

        persona = db.scalar(stmt)

        if not persona:
            raise HTTPException(
                status_code=404,
                detail="페르소나를 찾을 수 없습니다."
            )

        return persona

    # 현재 활성화 된 페르소나 계정 조회
    @staticmethod
    async def get_current_persona(db: Session, redis_client, user_id: UUID):
        persona_id = await PersonaReadService.get_current_active_persona_id(
            db=db,
            redis_client=redis_client,
            user_id=user_id
        )

        if not persona_id:
            raise HTTPException(
                status_code=400,
                detail="활성화된 페르소나가 없습니다."
            )

        return await PersonaReadService.get_persona_detail(
            db=db,
            user_id=user_id,
            persona_id=persona_id
        )


    # 현재 활성화 된 계정 가져오기 (DB 기준)
    @staticmethod
    async def get_current_active_persona_id(db: Session,redis_client, user_id: UUID) -> Optional[UUID]:
        # 이제 토큰을 기준으로 하므로 Redis 로직 삭제. 초기 로그인 용도로 DB에서 "on" 상태 조회
        stmt = select(Persona.id).where(
            Persona.user_id == user_id,
            Persona.preference_status == "on"
        )

        active_id = db.scalar(stmt)
        return active_id

    @staticmethod
    async def get_active_persona_id(db: Session, user_id: UUID) -> Optional[UUID]:
        """
        현재 유저의 활성 페르소나 ID를 DB에서 조회합니다.
        """
        stmt = select(Persona.id).where(Persona.user_id == user_id, Persona.preference_status == "on")
        return db.scalar(stmt)