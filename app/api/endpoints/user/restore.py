from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import User
from app.service.user.restore_service import account_restore_service

router = APIRouter()

@router.post("/users/me/restore", status_code=status.HTTP_200_OK)
async def restore_my_account(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    탈퇴 유예 기간(30일) 내에 로그인하여 회원 탈퇴를 철회하고 계정을 복구합니다.
    (로그인 JWT 토큰 필요)
    """
    await account_restore_service.restore_account(db=db, user_id=user.id)
    return {"message": "계정이 성공적으로 복구되었습니다."}