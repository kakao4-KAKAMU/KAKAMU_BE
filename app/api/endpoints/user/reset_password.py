import hashlib
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models import User, LocalAuth
from app.core.security import get_password_hash
from app.schemas.request.auth import PasswordResetRequest
from app.schemas.response.common import SuccessResponse
from app.core.firebase import verify_firebase_token

router = APIRouter()

@router.post("/local/reset-password", response_model=SuccessResponse)
def reset_local_password(
    request: PasswordResetRequest,
    db: Session = Depends(get_db)
):
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

    # 2. 인증된 전화번호를 기반으로 User 조회
    user = db.query(User).filter(User.phone == formatted_phone).first()
    
    if not user:
        raise HTTPException(
            status_code=404, 
            detail={"code": "USER_NOT_FOUND", "message": "해당 전화번호로 가입된 계정이 없습니다."}
        )

    # 3. 로컬 계정(이메일 가입자) 여부 확인
    local_auth = db.query(LocalAuth).filter(LocalAuth.user_id == user.id).first()
    if not local_auth:
        raise HTTPException(
            status_code=400,
            detail={"code": "SOCIAL_USER", "message": "소셜 로그인으로 가입된 계정입니다. 해당 소셜 서비스를 통해 로그인해주세요."}
        )

    # 4. 비밀번호 업데이트 (해싱 처리)
    local_auth.password_hash = get_password_hash(request.new_password)
    
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail={"code": "DB_COMMIT_ERROR", "message": "비밀번호 갱신 중 서버 오류가 발생했습니다."})
    
    return {"status": "success", "message": "비밀번호가 성공적으로 재설정되었습니다."}