import logging
from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from uuid import UUID
from datetime import datetime, timezone

from app.models import User, Persona, Post, Comment, LikeLog, Follow, FavMovie, FavGenre, FavPeople

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
            db.delete(user)
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