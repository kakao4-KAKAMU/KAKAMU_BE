import random
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import select, and_
from fastapi import HTTPException

from app.models.user import User
from app.schemas.request.user import UserUpdate

class UserUpdateService:
    async def update_user(self, db: Session, user_id: UUID, user_in: UserUpdate) -> User:
        user = db.query(User).filter(User.id == user_id, User.status == "ACTIVE").first()
        if not user:
            raise HTTPException(status_code=404, detail={"code": "USER_NOT_FOUND", "message": "사용자를 찾을 수 없습니다."})

        # 1. 닉네임 변경 요청 시 중복(닉네임+태그) 검사
        if user_in.nickname is not None and user_in.nickname != user.nickname:
            # 기존 태그를 그대로 사용할 수 있는지 우선 확인
            conflict = db.scalar(select(User).where(
                and_(User.nickname == user_in.nickname, User.tag == user.tag)
            ))
            
            if conflict:
                # 기존 태그와 충돌할 경우 새로운 4자리 랜덤 태그(0001~9999) 발급
                new_tag = None
                for _ in range(20): # 재시도 20회
                    candidate_tag = f"{random.randint(1, 9999):04d}"
                    if not db.scalar(select(User).where(
                        and_(User.nickname == user_in.nickname, User.tag == candidate_tag)
                    )):
                        new_tag = candidate_tag
                        break
                
                if not new_tag:
                    raise HTTPException(status_code=400, detail={"code": "NICKNAME_UNAVAILABLE", "message": "해당 닉네임은 현재 사용할 수 없습니다. (태그 발급 실패)"})
                
                user.tag = new_tag # 충돌을 피하기 위해 부득이하게 새로운 태그로 갱신
                
            user.nickname = user_in.nickname

        # 2. 프로필 이미지 변경
        if user_in.profile_image_url is not None:
            user.profile_image_url = user_in.profile_image_url

        try:
            db.commit()
            db.refresh(user)
            return user
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail={"code": "USER_UPDATE_FAILED", "message": "사용자 정보 수정 중 오류가 발생했습니다."})

user_update_service = UserUpdateService()