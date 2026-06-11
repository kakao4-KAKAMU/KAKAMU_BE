from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from uuid import UUID

from app.db.session import get_db
from app.schemas.response.user import UserResponse
from app.service.user.user import user_service
from app.schemas.errors import ERROR_USER_NOT_FOUND

router = APIRouter()

@router.get("/{user_id}", response_model=UserResponse, responses={404: ERROR_USER_NOT_FOUND})
def get_user_info_api(
    user_id: UUID,
    db: Session = Depends(get_db)
):
    """특정 유저의 상세 정보를 조회합니다."""
    return user_service.get_user(db=db, user_id=user_id)