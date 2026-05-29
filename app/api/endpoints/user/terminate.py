from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from uuid import UUID

from app.db.session import get_db
from app.api.deps import get_current_user # 프로젝트의 공통 유저 식별 의존성 사용
from app.service.user.terminate_service import account_termination_service

router = APIRouter()

@router.post("/v1/account/terminate", tags=["Account"])
async def terminate_account(
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user)
):
    """단일 트랜잭션 기반 회원 탈퇴 및 데이터 영구 파기"""
    await account_termination_service.terminate_account(db, user_id)
    
    return {"status": "success", "message": "회원 탈퇴 및 데이터 파기가 완료되었습니다."}