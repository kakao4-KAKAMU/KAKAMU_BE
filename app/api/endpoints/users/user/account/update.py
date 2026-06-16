from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.api.deps.auth import get_active_user
from app.models.user import User
from app.schemas.request.user import UserUpdate
from app.schemas.response.user import UserResponse
from app.service.user.update_user import user_update_service
from app.schemas.errors import (
    ERROR_UNAUTHORIZED,
    ERROR_VALIDATION_ERROR,
    ERROR_NICKNAME_UNAVAILABLE,
    ERROR_USER_NOT_FOUND,
    ERROR_USER_UPDATE_FAILED
)

router = APIRouter()

@router.put(
    "/me",
    response_model=UserResponse,
    responses={
        400: ERROR_NICKNAME_UNAVAILABLE,
        401: ERROR_UNAUTHORIZED,
        404: ERROR_USER_NOT_FOUND,
        422: ERROR_VALIDATION_ERROR,
        500: ERROR_USER_UPDATE_FAILED
    },
    summary="내 프로필 정보 수정"
)
async def update_my_profile(
    user_in: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_active_user)
) -> User:
    """내 계정(User)의 닉네임과 프로필 이미지를 수정합니다. (태그는 변경 불가)"""
    return await user_update_service.update_user(db, current_user.id, user_in)