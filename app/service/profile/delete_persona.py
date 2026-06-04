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
                detail={"code": "PERSONA_NOT_FOUND", "message": "페르소나를 찾을 수 없습니다."}
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
                detail={"code": "MINIMUM_PERSONA_REQUIRED", "message": "최소 1개의 페르소나는 유지해야 하므로 삭제할 수 없습니다."}
            )

        try:

            persona.status = "DELETED" # 페르소나 상태를 ACTIVE -> DELETED 로 변경
            persona.deleted_at = datetime.now(timezone.utc) # 현재 삭제 시도 시간 저장
            db.commit()

        except Exception as e:
            db.rollback()

            raise HTTPException(
                status_code=500,
                detail={"code": "PERSONA_DELETE_FAILED", "message": f"페르소나 삭제 중 오류 발생 : {str(e)}"}
            )

        return None

# * 7일 뒤 자동 삭제 로직은 app.worker.persona_batch 내 배치 작업(APScheduler)으로 구현됨.