from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import User
from app.schemas.response.common import SuccessResponse
from app.schemas.request.auth import PasswordChangeRequest
from app.api.deps.auth import get_active_user
from app.service.user.change_password_service import change_password_service

router = APIRouter()

@router.post(
    "/local/change-password",
    response_model=SuccessResponse,
    summary="비밀번호 변경 (로그인 후)"
)
def change_local_password(
    request: PasswordChangeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_active_user)
) -> dict:
    """
    로그인한 상태에서 기존 비밀번호를 확인하고 새로운 비밀번호로 변경합니다.
    일반 이메일/비밀번호 로그인이 연동된 사용자만 이용 가능합니다.
    """
    # 서비스 레이어로 비즈니스 로직 위임
    change_password_service.change_password(db, current_user.id, request)
    
    return {"status": "success", "message": "비밀번호가 성공적으로 변경되었습니다."}