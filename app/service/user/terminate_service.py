from datetime import datetime
from app.core.logging import logger
from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select, update
from uuid import UUID

from app.models import User, Persona, UserStatus, PersonaStatus

class AccountTerminationService:
    
    @staticmethod
    async def terminate_account(db: Session, user_id: UUID) -> bool:
        """
        회원 탈퇴 처리 (Soft Delete 전환 및 종속 페르소나 일괄 처리)
        """
        # 1. 유저 조회
        user = db.scalar(select(User).where(User.id == user_id, User.status == UserStatus.ACTIVE))
        if not user:
            raise HTTPException(status_code=404, detail={"code": "USER_NOT_FOUND", "message": "유저를 찾을 수 없습니다."})
            
        try:
            # 2. 소프트 삭제 처리를 위한 현재 시각 획득
            termination_time = datetime.now()
            
            # 3. 유저 상태를 DELETED로 변경하고 삭제 시점 기록
            user.status = UserStatus.DELETED
            user.deleted_at = termination_time
            
            # 4. 해당 유저가 소유한 ACTIVE 상태의 페르소나들도 일괄 DELETED 처리하며 삭제 시점을 동일하게 매핑
            db.execute(
                update(Persona)
                .where(
                    Persona.user_id == user_id,
                    Persona.status == PersonaStatus.ACTIVE
                )
                .values(
                    status=PersonaStatus.DELETED,
                    deleted_at=termination_time
                )
            )
            
            db.commit()
            return True

        except Exception as e:
            db.rollback()
            logger.error(f"[Termination Error] Failed to terminate account for user {user_id}: {e}")
            raise HTTPException(
                status_code=500, 
                detail={"code": "TERMINATION_FAILED", "message": "탈퇴 처리 중 예기치 않은 오류가 발생했습니다."}
            )

account_termination_service = AccountTerminationService()
