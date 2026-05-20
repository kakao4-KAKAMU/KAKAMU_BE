import redis

from app.core.redis import redis_client
import re
from fastapi import HTTPException, status
from sqlalchemy import select, and_, func, update
from sqlalchemy.orm import Session
from app.models.models import Persona
from app.schemas.profile import PersonaCreate

class PersonaReadService:

    async def activate_persona(db: Session,persona_id: id, user_id: int):
        db_persona = db.get(Persona,persona_id)
        THREE_DAY = 259200 # 3일 동안 활성화
        if not db_persona or db_persona.user_id != user_id:
            return False

        try: # 해당 유저의 모든 페르소나를 off로 전환하고
            db.execute(
                update(Persona).where(Persona.id == persona_id).values(preference_status="off")
            )
            db_persona.preference_status = "on" # 선택한 페르소나만 on으로 전환
            db.commit()

            redis_key = f"kakamu:user:{user_id}:current_persona"

            await redis_client.set(redis_key,persona_id, ex=THREE_DAY) # 3일동안 유지

        except Exception as e:
            db.rollback()
            return False



    # 현재 활성화 된 계정 가져오기 + 자동 기간 갱신
    @staticmethod
    async def get_current_active_persona_id(db: Session, user_id: int) -> int:
        redis_key = f"kakamu:user:{user_id}:current_persona"
        THREE_DAY = 259200

        # redis에 값이 있는지 확인
        cached_persona_id = await redis_client.get(redis_key)

        # redis에 값이 존재하면 만료 시간 3일 연장
        if cached_persona_id is not None:
            await redis_client.expire(redis_key, THREE_DAY)
            return int(cached_persona_id)

        # 만약 없으면 현재 "on" 상태의 페르소나 조회
        stmt = select(Persona).where(
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