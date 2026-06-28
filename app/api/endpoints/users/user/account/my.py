from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Optional

from app.db.session import get_db
from app.schemas.response.user import UserPublicResponse
from app.service.user.user import user_service
from app.schemas.errors import ERROR_USER_NOT_FOUND
from app.api.deps.auth import get_active_user
from app.models import User

router = APIRouter()


@router.get(
    "/me",
    response_model=UserPublicResponse,
    responses={404: ERROR_USER_NOT_FOUND},
    summary="내 프로필 정보 조회"
)
def get_user_info_api(
    db: Session = Depends(get_db), current_user: User = Depends(get_active_user)
) -> dict:
    """내 프로필 정보를 조회합니다. (태그는 변경 불가)"""
    return user_service.get_public_user(db=db, target_user_id=current_user.id, viewer_user_id=current_user.id)
