import redis

from app.core.redis import redis_client
import re
from fastapi import HTTPException, status
from sqlalchemy import select, and_, func, update
from sqlalchemy.orm import Session
from app.models.models import Persona
from app.schemas.profile import PersonaCreate, PersonaEdit

class PersonaService:
    def __init__(self):
        self.redis = redis_client

    # 특정 페르소나를 활성화
    async def activate_persona(self, db: Session, persona_id: int, user_id: int):
        db_persona = db.get(Persona,persona_id)
        THREE_DAY = 259200 # 3일 동안 활성화
        if not db_persona or db_persona.user_id != user_id:
            return False

        try: # 해당 유저의 모든 페르소나를 off로 전환하고
            db.execute(
                update(Persona).where(Persona.user_id == user_id).values(preference_status="off")
            )
            db_persona.preference_status = "on" # 선택한 페르소나만 on으로 전환
            db.commit()

            redis_key = f"kakamu:user:{user_id}:current_persona"

            await self.redis.set(redis_key,persona_id, ex=THREE_DAY) # 3일동안 유지

            return True
        except Exception as e:
            db.rollback()
            return False

    # 현재 활성화 된 계정 가져오기 + 자동 기간 갱신
    async def get_current_active_persona_id(self,db: Session, user_id: int) -> int:
        redis_key = f"kakamu:user:{user_id}:current_persona"
        THREE_DAY = 259200

        # redis에 값이 있는지 확인
        cached_persona_id = await self.redis.get(redis_key)

        # redis에 값이 존재하면 만료 시간 3일 연장
        if cached_persona_id is not None:
            await self.redis.expire(redis_key, THREE_DAY)
            return int(cached_persona_id)

        # 만약 없으면 현재 "on" 상태의 페르소나 조회
        stmt = select(Persona).where(
            Persona.user_id == user_id,
            Persona.preference_status == "on"
        )

        active_id = db.scalar(stmt)

        # 그 페르소나로 다시 redis에 등록
        if active_id:
            await self.redis.set(redis_key, active_id, ex=THREE_DAY)
            return active_id

        return None



    async def switch_persona(self, db: Session, user_id: int, persona_id: int):
        """
        유저의 현재 활성 페르소나를 변경합니다. (DB와 Redis 동기화)
        """
        db_persona = db.get(Persona, persona_id)
        if not db_persona or db_persona.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="페르소나를 찾을 수 없거나 권한이 없습니다.")

        try:
            # 해당 유저의 모든 페르소나 상태를 off로 초기화
            db.execute(
                update(Persona).where(Persona.user_id == user_id).values(preference_status="off")
            )
            # 선택한 페르소나만 on으로 변경
            db_persona.preference_status = "on"
            db.commit()

            key = f"kakamu:user:{user_id}:current_persona"
            # Redis에 유저별 현재 페르소나 ID 저장 (3일 유지)
            await self.redis.set(key, persona_id, ex=259200)
            return {"status": "success", "active_persona_id": persona_id}
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="페르소나 전환 중 오류가 발생했습니다.")
