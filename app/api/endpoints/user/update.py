from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.api.deps.auth import get_active_user
from app.models.user import User
from app.schemas.user import UserUpdate, UserResponse
from app.service.user.update_user import user_update_service

router = APIRouter()

@router.put("/me", response_model=UserResponse)
async def update_my_profile(
    user_in: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_active_user)
):
    """내 계정(User)의 닉네임과 프로필 이미지를 수정합니다. (태그는 변경 불가)"""
    return await user_update_service.update_user(db, current_user.id, user_in)