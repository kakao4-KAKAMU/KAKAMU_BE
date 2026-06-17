from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.api.deps import get_active_user
from app.models import User
from app.schemas.response.common import SuccessResponse
from app.service.user.terminate_service import account_termination_service

router = APIRouter()

@router.post(
    "/me/terminate",
    tags=["Account"],
    response_model=SuccessResponse,
    summary="회원 탈퇴 요청 (소프트 삭제)"
)
async def terminate_account(
    db: Session = Depends(get_db),
    user: User = Depends(get_active_user)
) -> dict:
    """회원 탈퇴 시 즉시 데이터를 삭제하지 않고 7일간 유예(Soft Delete)합니다."""
    await account_termination_service.terminate_account(db, user.id)
    
    return {"status": "success", "message": "회원 탈퇴 처리가 완료되었습니다. 7일 후 데이터가 영구 파기됩니다."}