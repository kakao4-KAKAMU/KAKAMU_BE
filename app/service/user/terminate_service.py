import logging
from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from uuid import UUID
from datetime import datetime, timezone

from app.models import User, Persona, Post, Comment, LikeLog, Follow, FavMovie, FavGenre, FavPeople, EntityRelationshipLog

logger = logging.getLogger(__name__)

class AccountTerminationService:
    
    @staticmethod
    async def terminate_account(db: Session, user_id: UUID) -> bool:
        """
        회원 탈퇴 및 데이터 파기 (Atomic Transaction 보장)
        """
        # 1. 유저 및 종속 페르소나 조회
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail={"code": "USER_NOT_FOUND", "message": "유저를 찾을 수 없습니다."})
            
        try:
            now = datetime.now(timezone.utc)
            
            # 1. 유저 계정 Soft Delete 처리
            user.status = "DELETED"
            user.deleted_at = now

            # 2. 보유한 모든 활성 페르소나도 함께 Soft Delete 처리
            db.query(Persona).filter(
                Persona.user_id == user_id,
                Persona.status == "ACTIVE"
            ).update({
                "status": "DELETED",
                "deleted_at": now
            }, synchronize_session=False)

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