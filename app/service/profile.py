from sqlalchemy.orm import Session,selectinload
from fastapi import HTTPException
from app.models.models import User


def get_user_with_profiles(db: Session, user_id: int):
    # N+1 쿼리 문제 방지를 위해 , User 테이블의 profiles 관계를 한번에 가져옴
    user = db.query(User).options(selectinload(User.profiles)).filter(User.id == user_id).first()
    # user가 없으면 404 에러 반환
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user