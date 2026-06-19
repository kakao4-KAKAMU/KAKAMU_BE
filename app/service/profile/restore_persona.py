from fastapi import HTTPException
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app.models import Persona
from app.schemas.base.persona import Persona as PersonaSchema
from app.schemas.mapper.persona import PersonaMapper
from uuid import UUID

class PersonaRestoreService:

    @staticmethod
    async def restore_persona(
        db: Session,
        user_id: UUID,
        persona_id: UUID
    ) -> PersonaSchema:
        stmt = select(Persona).where(
            Persona.id == persona_id,
            Persona.user_id == user_id
        )
        persona = db.scalar(stmt)

        if not persona:
            raise HTTPException(
                status_code=404,
                detail={"code": "PERSONA_NOT_FOUND", "message": "페르소나를 찾을 수 없습니다."}
            )

        if persona.status == "ACTIVE":
            raise HTTPException(
                status_code=400,
                detail={"code": "ALREADY_ACTIVE", "message": "이미 활성화된 페르소나입니다."}
            )

        # 활성 페르소나 개수 확인 (최대 5개 제한)
        count_stmt = select(func.count(Persona.id)).where(
            Persona.user_id == user_id,
            Persona.status == "ACTIVE"
        )
        active_persona_count = db.scalar(count_stmt)

        if active_persona_count >= 5:
            raise HTTPException(
                status_code=400,
                detail={"code": "PERSONA_LIMIT_EXCEEDED", "message": "페르소나 계정은 최대 5개까지만 활성화할 수 있습니다."}
            )

        try:
            # DELETED -> ACTIVE 변경 및 삭제 예약 취소
            persona.status = "ACTIVE"
            persona.deleted_at = None
            db.commit()
            db.refresh(persona)
            return PersonaMapper.to_persona(persona)
            
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=500,
                detail={"code": "PERSONA_RESTORE_FAILED", "message": f"페르소나 복구 중 오류 발생 : {str(e)}"}
            )