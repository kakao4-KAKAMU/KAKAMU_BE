from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.register.social import SocialRegisterRequest
from app.schemas.login.social import TokenResponse
from app.models.models import User, SocialAuth
from app.core.security import create_access_token, create_refresh_token
from app.api.deps import validate_social_registration

router = APIRouter()

@router.post("/social", response_model=TokenResponse)
def register_social_user(db: Session = Depends(get_db), val_data: dict = Depends(validate_social_registration)):
    """추가 정보를 받아 User와 SocialAuth를 생성하고 JWT를 발급합니다."""
    request: SocialRegisterRequest = val_data["request"]
    try:
        db_user = db.query(User).filter(User.ci_value == val_data["ci_value"]).first()
        if not db_user:
            db_user = User(username=request.username, nickname=request.nickname, phone=request.phone, ci_value=val_data["ci_value"])
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
