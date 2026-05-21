import redis

import re
from fastapi import HTTPException, status
from sqlalchemy import select, and_, func, update
from sqlalchemy.orm import Session
from app.models.models import Persona
from app.schemas.profile import PersonaCreate
from typing import List

class PersonaReadService:

    # 내 모든 페르소나 조회
    @staticmethod
    async def get_my_personas(db: Session, user_id: int) -> List[Persona]:
        stmt = select(Persona).where(
            Persona.user_id == user_id,
            Persona.status != "DELETED"
        )

        return list(db.scalars(stmt).all())

    # 특정 페르소나 조회
    @staticmethod
    async def get_persona_detail(
        db: Session,
        user_id: int,
        persona_id: int
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
    async def get_current_persona(db: Session, redis_client, user_id: int):
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


    # 현재 활성화 된 계정 가져오기 + 자동 기간 갱신
    @staticmethod
    async def get_current_active_persona_id(db: Session,redis_client, user_id: int) -> int:
        redis_key = f"kakamu:user:{user_id}:current_persona"
        THREE_DAY = 259200

        # redis에 값이 있는지 확인
        cached_persona_id = await redis_client.get(redis_key)

        # redis에 값이 존재하면 만료 시간 3일 연장
        if cached_persona_id is not None:
            await redis_client.expire(redis_key, THREE_DAY)
            return int(cached_persona_id)

        # 만약 없으면 현재 "on" 상태의 페르소나 조회 후 페르소나 id만 조회
        stmt = select(Persona.id).where(
            Persona.user_id == user_id,
            Persona.preference_status == "on"
        )

        active_id = db.scalar(stmt)

        # 그 페르소나로 다시 redis에 등록
        if active_id:
            await redis_client.set(redis_key,active_id, ex=THREE_DAY)
            return active_id

        return None

    @staticmethod
    async def get_active_persona_id(redis_client,user_id: int):
        """
        현재 유저가 어떤 페르소나로 접속 중인지 가져옵니다.
        """
        key = f"kakamu:user:{user_id}:current_persona"
        persona_id = await redis_client.get(key)
        return int(persona_id) if persona_id else None