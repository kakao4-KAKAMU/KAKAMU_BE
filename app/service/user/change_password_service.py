from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from uuid import UUID

from app.models import LocalAuth
from app.core.security import get_password_hash, verify_password
from app.schemas.request.auth import PasswordChangeRequest

class ChangePasswordService:
    
    @staticmethod
    def change_password(db: Session, user_id: UUID, request: PasswordChangeRequest) -> None:
        # 1. LocalAuth에 정보가 있는지 확인 (소셜 로그인 전용 사용자 차단)
        local_auth = db.scalar(select(LocalAuth).where(LocalAuth.user_id == user_id))
        if not local_auth:
            raise HTTPException(
                status_code=400, 
                detail={"code": "SOCIAL_USER_CANNOT_CHANGE_PASSWORD", "message": "소셜 전용 계정은 비밀번호를 변경할 수 없습니다. 이메일 연동 후 이용해주세요."}
            )

        # 2. 현재 비밀번호 검증
        if not verify_password(request.current_password, local_auth.password_hash):
            raise HTTPException(status_code=401, detail={"code": "INVALID_CURRENT_PASSWORD", "message": "현재 비밀번호가 일치하지 않습니다."})

        # 3. 새 비밀번호 중복 검증
        if verify_password(request.new_password, local_auth.password_hash):
            raise HTTPException(status_code=400, detail={"code": "SAME_PASSWORD", "message": "새 비밀번호는 기존 비밀번호와 다르게 설정해야 합니다."})

        # 4. 비밀번호 갱신
        local_auth.password_hash = get_password_hash(request.new_password)
        try:
            db.commit()
        except Exception:
            db.rollback()
            raise HTTPException(status_code=500, detail={"code": "DB_COMMIT_ERROR", "message": "비밀번호 갱신 중 오류가 발생했습니다."})

change_password_service = ChangePasswordService()