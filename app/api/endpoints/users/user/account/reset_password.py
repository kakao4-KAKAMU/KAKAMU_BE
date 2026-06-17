import re
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from pydantic import BaseModel, validator, EmailStr

from app.db.session import get_db
from app.models import User, LocalAuth
from app.core.security import get_password_hash
from app.schemas.response.common import SuccessResponse
from app.core.firebase import verify_firebase_token
from app.schemas.errors import (
    ERROR_USER_NOT_FOUND,
    ERROR_RESET_PASSWORD_FAILURES,
    ERROR_VALIDATION_ERROR,
    ERROR_DB_COMMIT_ERROR
)

router = APIRouter()

class PasswordResetRequest(BaseModel):
    email: EmailStr
    firebase_id_token: str
    new_password: str

    @validator("new_password")
    def validate_password_complexity(cls, v: str) -> str:
        """비밀번호 복잡도 검증: 8자 이상, 영문, 숫자 포함"""
        errors = []
        if len(v) < 8:
            errors.append("8자 이상")
        if not re.search(r"[a-zA-Z]", v):
            errors.append("영문")
        if not re.search(r"\d", v):
            errors.append("숫자")
        
        if errors:
            raise ValueError(f"비밀번호는 다음 조건을 만족해야 합니다: {', '.join(errors)} 포함")
        return v

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
    # 1. Firebase 토큰 검증 및 전화번호 추출
    phone_number = verify_firebase_token(request.firebase_id_token)
    if not phone_number:
        raise HTTPException(
            status_code=400, 
            detail={"code": "INVALID_FIREBASE_TOKEN", "message": "유효하지 않거나 만료된 Firebase 토큰입니다."}
        )
        
    formatted_phone = phone_number.replace("+82", "0") if phone_number.startswith("+82") else phone_number

    # 2. 이메일(LocalAuth)과 전화번호(User)를 동시에(JOIN) 검증하여 안전하게 계정 찾기
    local_auth = db.scalar(
        select(LocalAuth)
        .join(User, LocalAuth.user_id == User.id)
        .where(LocalAuth.email == request.email)
        .where(User.phone == formatted_phone)
    )
    if not local_auth:
        raise HTTPException(
            status_code=404, 
            detail={"code": "USER_NOT_FOUND", "message": "입력하신 이메일과 인증된 전화번호가 일치하는 계정을 찾을 수 없습니다."}
        )

    # 4. 비밀번호 업데이트 (해싱 처리)
    local_auth.password_hash = get_password_hash(request.new_password)
    
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail={"code": "DB_COMMIT_ERROR", "message": "비밀번호 갱신 중 서버 오류가 발생했습니다."})
    
    return {"status": "success", "message": "비밀번호가 성공적으로 재설정되었습니다."}