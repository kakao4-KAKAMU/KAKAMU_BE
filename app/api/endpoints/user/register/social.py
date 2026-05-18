from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.register.social import SocialRegisterRequest
from app.schemas.login.social import TokenResponse
from app.models.models import User, SocialAuth
from app.core.security import create_access_token, create_refresh_token
from app.api.deps import validate_social_registration, get_current_user

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
def link_social_user(
    db: Session = Depends(get_db), 
    val_data: dict = Depends(validate_social_registration),
    current_user: User = Depends(get_current_user)
):
    """로그인된 상태에서 전화번호 재인증을 거쳐 소셜 계정을 추가 연동합니다."""
    request: SocialRegisterRequest = val_data["request"]
    ci_value = val_data["ci_value"]
    
    # 1. 로그인된 유저의 본인인증 정보와 일치하는지 검증 (타인 명의 연동 차단)
    if current_user.ci_value != ci_value:
        raise HTTPException(status_code=400, detail={"code": "CI_MISMATCH", "message": "입력하신 본인인증 정보가 현재 로그인된 계정의 정보와 일치하지 않습니다."})
        
    # 2. 이미 같은 소셜 플랫폼이 연동되어 있는지 확인
    existing_social = db.query(SocialAuth).filter(SocialAuth.user_id == current_user.id, SocialAuth.provider == request.provider).first()
    if existing_social:
        raise HTTPException(status_code=400, detail={"code": "SOCIAL_AUTH_ALREADY_LINKED", "message": "이미 연동된 소셜 계정입니다."})
        
    db.add(SocialAuth(user_id=current_user.id, provider=request.provider, provider_user_id=val_data["provider_user_id"], email=request.email))
    db.commit()
    
    return TokenResponse(access_token=create_access_token(data={"sub": str(current_user.id)}), refresh_token=create_refresh_token(data={"sub": str(current_user.id)}), is_new_user=False)
