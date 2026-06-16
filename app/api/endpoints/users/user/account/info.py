from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Optional

from app.db.session import get_db
from app.schemas.response.user import UserPublicResponse
from app.service.user.user import user_service
from app.schemas.errors import ERROR_USER_NOT_FOUND
from app.api.deps.auth import get_optional_user
from app.models import User

router = APIRouter()

@router.get(
    "/{user_id}",
    response_model=UserPublicResponse,
    responses={404: ERROR_USER_NOT_FOUND},
    summary="유저 상세 정보 조회"
)
def get_user_info_api(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
) -> dict:
    """특정 유저의 상세 정보를 조회합니다. (비회원 접근 가능)"""
    viewer_id = current_user.id if current_user else None
    return user_service.get_public_user(db=db, target_user_id=user_id, viewer_user_id=viewer_id)