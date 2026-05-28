import hashlib
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models import User, LocalAuth
from app.core.security import get_password_hash
from app.schemas.login.reset import PasswordResetRequest
from app.core.firebase import verify_firebase_token

router = APIRouter()

@router.post("/local/reset-password")
def reset_local_password(
    request: PasswordResetRequest,
    db: Session = Depends(get_db)
):
    """
    Firebase 본인 인증(전화번호)을 통해 이메일 계정의 비밀번호를 재설정합니다.
    """
    # 1. 이메일로 LocalAuth 및 User 정보 동시 조회 (DB 접근 최적화)
    result = db.query(LocalAuth, User).join(User, LocalAuth.user_id == User.id).filter(LocalAuth.email == request.email).first()
    if not result:
        raise HTTPException(
            status_code=404, 
            detail={"code": "USER_NOT_FOUND", "message": "해당 이메일로 가입된 계정을 찾을 수 없습니다."}
        )
    
    local_auth, user = result

    # 2. Firebase 토큰 검증 및 본인 확인
    phone_number = verify_firebase_token(request.firebase_id_token)
    if not phone_number:
        raise HTTPException(
            status_code=400, 
            detail={"code": "INVALID_FIREBASE_TOKEN", "message": "유효하지 않거나 만료된 Firebase 토큰입니다."}
        )
        
    formatted_phone = phone_number.replace("+82", "0") if phone_number.startswith("+82") else phone_number
    ci_string = f"{user.username}{formatted_phone}"
    ci_value = hashlib.sha256(ci_string.encode('utf-8')).hexdigest()

    if user.ci_value != ci_value:
        raise HTTPException(
            status_code=403, 
            detail={"code": "AUTH_MISMATCH", "message": "본인 인증 정보가 일치하지 않습니다."}
        )

    # 3. 비밀번호 업데이트 (해싱 처리)
    local_auth.password_hash = get_password_hash(request.new_password)
    db.commit()
    
    return {"status": "success", "message": "비밀번호가 성공적으로 재설정되었습니다."}