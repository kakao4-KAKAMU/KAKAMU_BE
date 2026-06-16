from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.api.deps import get_active_user
from app.models import User
from app.schemas.response.common import SuccessResponse
from app.service.user.terminate_service import account_termination_service

router = APIRouter()

@router.post(
    "/v1/account/terminate",
    tags=["Account"],
    response_model=SuccessResponse,
    summary="회원 탈퇴 및 데이터 파기"
)
async def terminate_account(
    db: Session = Depends(get_db),
    user: User = Depends(get_active_user)
) -> dict:
    """단일 트랜잭션 기반 회원 탈퇴 및 데이터 영구 파기"""
    await account_termination_service.terminate_account(db, user.id)
    
    return {"status": "success", "message": "회원 탈퇴 및 데이터 파기가 완료되었습니다."}