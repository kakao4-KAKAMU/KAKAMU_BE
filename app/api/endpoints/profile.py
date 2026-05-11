from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.profile import UserWithProfileResponse
from app.service import profile as profile_service

router = APIRouter()

@router.get("/{user_id}", response_model=UserWithProfileResponse)
def read_user_profile(user_id: int, db: Session = Depends(get_db)):
    """
    ### 1. 프로필 조회
    - 특정 사용자의 기본 정보와 생성된 페르소나(프로필) 목록을 함께 조회합니다.
    """
    return profile_service.get_user_with_profiles(db=db, user_id=user_id)