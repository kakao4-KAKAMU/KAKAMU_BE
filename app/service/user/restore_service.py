from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select, update
from uuid import UUID
from app.models import User, Persona

class AccountRestoreService:
    
    @staticmethod
    async def restore_account(db: Session, user_id: UUID) -> bool:
        """
        회원 탈퇴(Soft Delete) 취소 및 계정 복구
        """
        user = db.scalar(select(User).where(User.id == user_id))
        
        if not user:
            raise HTTPException(status_code=404, detail={"code": "USER_NOT_FOUND", "message": "유저를 찾을 수 없습니다."})
            
        if user.status == "ACTIVE":
            raise HTTPException(status_code=400, detail={"code": "ALREADY_ACTIVE", "message": "이미 활성화된 계정입니다."})

        try:
            user_deleted_at = user.deleted_at
            
            # 1. 유저 계정 상태 복원
            user.status = "ACTIVE"
            user.deleted_at = None

            # 2. 회원 탈퇴 시 함께 삭제(Soft Delete)되었던 페르소나 일괄 복원
            # (deleted_at 값이 유저의 탈퇴 시점과 정확히 일치하는 데이터만 복구하여 그 전에 따로 지웠던 페르소나 방어)
            if user_deleted_at:
                db.execute(update(Persona).where(
                    Persona.user_id == user_id,
                    Persona.status == "DELETED",
                    Persona.deleted_at == user_deleted_at
                ).values(status="ACTIVE", deleted_at=None))

            db.commit()
            return True

        except Exception:
            db.rollback()
            raise HTTPException(
                status_code=500, 
                detail={"code": "RESTORE_FAILED", "message": "계정 복구 중 예기치 않은 오류가 발생했습니다."}
            )

account_restore_service = AccountRestoreService()