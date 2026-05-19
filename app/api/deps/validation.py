import hashlib
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.models import LocalAuth, SocialAuth
from app.schemas.register.local import UserRegister
from app.schemas.register.social import SocialRegisterRequest
from app.core.firebase import verify_firebase_token
from app.service.social_auth import get_kakao_user_info

def validate_local_registration(user_in: UserRegister, db: Session = Depends(get_db)) -> dict:
    """일반 회원가입 시 Firebase 검증 및 이메일 중복을 체크하는 미들웨어 의존성"""
    phone_number = verify_firebase_token(user_in.firebase_id_token)
    if not phone_number:
        raise HTTPException(status_code=400, detail={"code": "INVALID_FIREBASE_TOKEN", "message": "Invalid or expired Firebase token"})
        
    formatted_phone = phone_number.replace("+82", "0") if phone_number.startswith("+82") else phone_number
    ci_string = f"{user_in.username}{formatted_phone}"
    ci_value = hashlib.sha256(ci_string.encode('utf-8')).hexdigest()
    
    if db.query(LocalAuth).filter(LocalAuth.email == user_in.email).first():
        raise HTTPException(status_code=400, detail={"code": "DUPLICATE_EMAIL", "message": "Email already registered"})
        
    return {
        "user_in": user_in,
        "formatted_phone": formatted_phone,
        "ci_value": ci_value
    }

async def validate_social_registration(request: SocialRegisterRequest, db: Session = Depends(get_db)) -> dict:
    """소셜 회원가입 시 토큰을 검증하고, 이메일 중복 체크 및 CI 값을 생성하는 미들웨어 의존성"""
    if request.provider == "kakao":
        user_info = await get_kakao_user_info(request.provided_token)
        provider_user_id = str(user_info.get("id"))
        if not provider_user_id or provider_user_id == "None":
            raise HTTPException(status_code=401, detail={"code": "INVALID_SOCIAL_TOKEN", "message": "유효하지 않은 소셜 토큰입니다."})
    else:
        raise HTTPException(status_code=400, detail={"code": "UNSUPPORTED_PROVIDER", "message": "지원하지 않는 소셜 플랫폼입니다."})

    # 2. Firebase 전화번호 검증 (조작 방지)
    phone_number = verify_firebase_token(request.firebase_id_token)
    if not phone_number:
        raise HTTPException(status_code=400, detail={"code": "INVALID_FIREBASE_TOKEN", "message": "Invalid or expired Firebase token"})
        
    formatted_phone = phone_number.replace("+82", "0") if phone_number.startswith("+82") else phone_number
    ci_string = f"{request.username}{formatted_phone}"
    ci_value = hashlib.sha256(ci_string.encode('utf-8')).hexdigest()
    
    if request.email and db.query(SocialAuth).filter(SocialAuth.provider == request.provider, SocialAuth.email == request.email).first():
        raise HTTPException(status_code=400, detail={"code": "DUPLICATE_EMAIL", "message": "이미 등록된 이메일입니다."})
        
    return {"request": request, "provider_user_id": provider_user_id, "ci_value": ci_value, "formatted_phone": formatted_phone}