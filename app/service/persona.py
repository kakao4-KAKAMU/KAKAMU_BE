import re
from fastapi import HTTPException, status
from sqlalchemy import select, and_, func, update
from sqlalchemy.orm import Session
from app.models import Persona
from app.schemas.profile import PersonaCreate, PersonaEdit
from uuid import UUID
from typing import Optional
from app.core.security import create_access_token

class PersonaService:
    # 특정 페르소나를 활성화
    async def activate_persona(self, db: Session, persona_id: UUID, user_id: UUID):
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

            return True
        except Exception as e:
            db.rollback()
            return False

    # 현재 활성화 된 계정 가져오기 + 자동 기간 갱신
    async def get_current_active_persona_id(self,db: Session, user_id: UUID) -> Optional[UUID]:
        # 만약 없으면 현재 "on" 상태의 페르소나 조회
        stmt = select(Persona).where(
            Persona.user_id == user_id,
            Persona.preference_status == "on"
        )

        active_id = db.scalar(stmt)
        return active_id



    async def switch_persona(self, db: Session, user_id: UUID, persona_id: UUID):
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

            # 변경된 페르소나 ID를 담아 새로운 액세스 토큰 발급
            new_access_token = create_access_token(data={"sub": str(user_id), "persona_id": str(persona_id)})
            return {
                "status": "success",
                "active_persona_id": persona_id,
                "access_token": new_access_token,
                "token_type": "bearer"
            }
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="페르소나 전환 중 오류가 발생했습니다.")
