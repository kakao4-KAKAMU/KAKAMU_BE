from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.request.auth import SocialRegisterRequest, SocialLinkRequest
from app.schemas.response.auth import TokenResponse
from app.models import User, SocialAuth
from app.core.security import create_access_token, create_refresh_token
from app.api.deps import validate_social_registration, get_current_user
from app.service.user.social_auth import get_kakao_user_info

router = APIRouter()

@router.post("/social", response_model=TokenResponse)
def register_social_user(db: Session = Depends(get_db), val_data: dict = Depends(validate_social_registration)):
    """추가 정보를 받아 User와 SocialAuth를 생성하고 JWT를 발급합니다."""
    request: SocialRegisterRequest = val_data["request"]
    try:
        db_user = db.query(User).filter(User.ci_value == val_data["ci_value"]).first()
        if not db_user:
            db_user = User(username=request.username, nickname=request.nickname, phone=val_data["formatted_phone"], ci_value=val_data["ci_value"])
            db.add(db_user)
            db.flush()
        else:
            # 중복 차단: 이미 동일한 Provider가 연결된 상태라면 진행 차단
            existing_social = db.query(SocialAuth).filter(
                SocialAuth.user_id == db_user.id,
                SocialAuth.provider == request.provider
            ).first()
            if existing_social:
                raise HTTPException(status_code=400, detail={"code": "SOCIAL_AUTH_ALREADY_LINKED", "message": "이미 연결된 계정입니다"})
        
        db.add(SocialAuth(user_id=db_user.id, provider=request.provider, provider_user_id=val_data["provider_user_id"], email=request.email))
        db.commit()
        return TokenResponse(access_token=create_access_token(data={"sub": str(db_user.id)}), refresh_token=create_refresh_token(data={"sub": str(db_user.id)}), is_new_user=False)
    except Exception as e:
        db.rollback()
        if isinstance(e, HTTPException): raise e
        raise HTTPException(status_code=500, detail={"code": "REGISTRATION_FAILED", "message": f"An unexpected error occurred: {str(e)}"})

@router.post("/social/link", response_model=TokenResponse)
async def link_social_user(
    request: SocialLinkRequest,
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """로그인된 상태에서 소셜 계정을 추가 연동합니다. (본인인증 생략)"""
    
    # 1. 소셜 토큰 검증 및 provider_user_id 추출
    if request.provider == "kakao":
        user_info = await get_kakao_user_info(request.provided_token)
        provider_user_id = str(user_info.get("id"))
        if not provider_user_id or provider_user_id == "None":
            raise HTTPException(status_code=401, detail={"code": "INVALID_SOCIAL_TOKEN", "message": "유효하지 않은 소셜 토큰입니다."})
    else:
        raise HTTPException(status_code=400, detail={"code": "UNSUPPORTED_PROVIDER", "message": "지원하지 않는 소셜 플랫폼입니다."})

    # 2. 이미 같은 소셜 플랫폼이 연동되어 있는지 확인
    existing_social = db.query(SocialAuth).filter(SocialAuth.user_id == current_user.id, SocialAuth.provider == request.provider).first()
    if existing_social:
        raise HTTPException(status_code=400, detail={"code": "SOCIAL_AUTH_ALREADY_LINKED", "message": "이미 연동된 소셜 계정입니다."})
        
    # 3. 해당 소셜 계정이 이미 다른 사용자와 연동되어 있는지 확인
    duplicate_social = db.query(SocialAuth).filter(SocialAuth.provider == request.provider, SocialAuth.provider_user_id == provider_user_id).first()
    if duplicate_social:
        raise HTTPException(status_code=400, detail={"code": "SOCIAL_ACCOUNT_ALREADY_USED", "message": "이 소셜 계정은 이미 다른 사용자와 연동되어 있습니다."})
        
    db.add(SocialAuth(user_id=current_user.id, provider=request.provider, provider_user_id=provider_user_id, email=request.email))
    db.commit()
    
    return TokenResponse(access_token=create_access_token(data={"sub": str(current_user.id)}), refresh_token=create_refresh_token(data={"sub": str(current_user.id)}), is_new_user=False)
