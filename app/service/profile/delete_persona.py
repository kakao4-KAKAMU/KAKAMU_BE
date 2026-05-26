from datetime import datetime,timezone

import redis

from app.core.redis import redis_client
import re
from fastapi import HTTPException, status
from sqlalchemy import select, and_, func, update
from sqlalchemy.orm import Session
from app.models import Persona
from app.schemas.profile import PersonaCreate

class PersonaDeleteService:


    @staticmethod
    async def delete_persona_soft(
            db: Session,
            redis_client,
            user_id: int,
            persona_id: int
    ):

        redis_key = f"kakamu:user:{user_id}:current_persona"
        THREE_DAY = 259200

        stmt = select(Persona).where(
            Persona.id == persona_id,
            Persona.user_id == user_id,
            Persona.status == "ACTIVE"
        )

        persona = db.scalar(stmt)

        if not persona:
            raise HTTPException(
                status_code=404,
                detail = "페르소나를 찾을 수 없습니다."
            )
        # 삭제 시도하는 페르소나가 메인 페르소나인지 확인
        if persona.is_main == 1:
            raise HTTPException(
                status_code=400,
                detail = f"메인 페르소나는 삭제 못합니다."
            )

        try:

            persona.status = "DELETED" # 페르소나 상태를 ACTIVE -> DELETED 로 변경
            persona.deleted_at = datetime.now(timezone.utc) # 현재 삭제 시도 시간 저장
            persona.preference_status = "off" # 활성화 상태를 off 로 변경

            # db.commit() # 현재 페르소나랑 관계없이 다 삭제 가능하다면 주석 제거
            current_persona_id = await redis_client.get(redis_key) # redis에 저장된 페르소나 id를 가져옴

            # 삭제 시도하는 페르소나 id와 현재 활성화 된 페르소나 id를 비교
            if current_persona_id and int(current_persona_id) == persona_id:

                # 페르소나 삭제 이후에는 메인 페르소나로 자동 전환
                remain_stmt = select(Persona).where(
                    Persona.is_main == 1,
                    Persona.user_id == user_id
                )


                remain_persona = db.scalar(remain_stmt)

                remain_persona.preference_status = "on"
                db.commit()

                # 현재 페르소나 (메인), redis에 저장
                await redis_client.set(redis_key,
                                       remain_persona.id,
                                       ex=THREE_DAY)

        except Exception as e:
            db.rollback()

            raise HTTPException(
                status_code=500,
                detail=f"페르소나 삭제 중 오류 발생 : {str(e)}"
            )

        return None



# 1번 페르소나를 활성화 하고 있는데 2번 페르소나 삭제를 할 수 있는가?
# 삭제된 페르소나는 페르소나 생성 규칙인 최대 5개에 포함되는 가?
# 즉시 페르소나 삭제 기능은 필요한가?
# 30일 뒤에 자동으로 삭제되도록 하려면 어떻게 해야하는가?