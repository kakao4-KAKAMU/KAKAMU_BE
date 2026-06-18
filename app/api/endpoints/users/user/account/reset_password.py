from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.response.common import SuccessResponse
from app.schemas.request.auth import PasswordResetRequest
from app.schemas.errors import (
    ERROR_USER_NOT_FOUND,
    ERROR_RESET_PASSWORD_FAILURES,
    ERROR_VALIDATION_ERROR,
    ERROR_DB_COMMIT_ERROR
)
from app.service.user.reset_password_service import reset_password_service

router = APIRouter()

@router.post(
    "/local/reset-password",
    response_model=SuccessResponse,
    responses={
        400: ERROR_RESET_PASSWORD_FAILURES,
        404: ERROR_USER_NOT_FOUND,
        422: ERROR_VALIDATION_ERROR,
        500: ERROR_DB_COMMIT_ERROR
    },
    summary="비밀번호 재설정"
)
def reset_local_password(
    request: PasswordResetRequest,
    db: Session = Depends(get_db)
) -> dict:
    """
    Firebase 본인 인증(전화번호)을 통해 이메일 계정의 비밀번호를 재설정합니다.
    """
    reset_password_service.reset_password(db, request)
    
    return {"status": "success", "message": "비밀번호가 성공적으로 재설정되었습니다."}