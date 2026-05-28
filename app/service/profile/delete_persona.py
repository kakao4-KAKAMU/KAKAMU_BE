from datetime import datetime,timezone
from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app.models import Persona
from uuid import UUID

class PersonaDeleteService:


    @staticmethod
    async def delete_persona_soft(
            db: Session,
            user_id: UUID,
            persona_id: UUID
    ):

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

        # 남은 활성 페르소나 개수 확인 (최소 1개는 유지)
        count_stmt = select(func.count(Persona.id)).where(
            Persona.user_id == user_id,
            Persona.status == "ACTIVE"
        )
        active_persona_count = db.scalar(count_stmt)

        if active_persona_count <= 1:
            raise HTTPException(
                status_code=400,
                detail="최소 1개의 페르소나는 유지해야 하므로 삭제할 수 없습니다."
            )

        try:

            persona.status = "DELETED" # 페르소나 상태를 ACTIVE -> DELETED 로 변경
            persona.deleted_at = datetime.now(timezone.utc) # 현재 삭제 시도 시간 저장
            db.commit()

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