from fastapi import HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from app.models import User

class UserService:
    
    @staticmethod
    def get_user(db: Session, user_id: UUID) -> User:
        """특정 유저의 정보를 데이터베이스에서 조회합니다."""
        user = db.query(User).filter(User.id == user_id, User.status == "ACTIVE").first()
        
        if not user:
            raise HTTPException(status_code=404, detail={"code": "USER_NOT_FOUND", "message": "요청한 사용자를 찾을 수 없습니다."})
            
        return user

user_service = UserService()