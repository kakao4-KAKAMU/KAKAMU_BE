from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select, and_
from app.db.session import get_db
from app.schemas.request.auth import SocialRegisterRequest, SocialLinkRequest
from app.schemas.response.auth import TokenResponse
from app.models import User, SocialAuth
from app.core.security import create_access_token, create_refresh_token
from app.api.deps import validate_social_registration, get_current_user
from app.service.user.social_auth import get_kakao_user_info
from app.schemas.errors import (
    ERROR_SOCIAL_AUTH_ALREADY_LINKED,
    ERROR_REGISTRATION_FAILED,
    ERROR_SOCIAL_LINK_FAILURES,
    ERROR_INVALID_SOCIAL_TOKEN
)

router = APIRouter()

@router.post(
    "/social",
    response_model=TokenResponse,
    responses={400: ERROR_SOCIAL_AUTH_ALREADY_LINKED, 500: ERROR_REGISTRATION_FAILED},
    summary="소셜 회원가입"
)
def register_social_user(db: Session = Depends(get_db), val_data: dict = Depends(validate_social_registration)) -> TokenResponse:
    """추가 정보를 받아 User와 SocialAuth를 생성하고 JWT를 발급합니다."""
    request: SocialRegisterRequest = val_data["request"]
    try:
        db_user = db.scalar(select(User).where(User.ci_value == val_data["ci_value"]))
        if not db_user:
            db_user = User(username=request.username, nickname=request.nickname, phone=val_data["formatted_phone"], ci_value=val_data["ci_value"])
            db.add(db_user)
            db.flush()
        else:
            # 중복 차단: 이미 동일한 Provider가 연결된 상태라면 진행 차단
            existing_social = db.scalar(select(SocialAuth).where(
                SocialAuth.user_id == db_user.id,
                SocialAuth.provider == request.provider
            ))
            if existing_social:
                raise HTTPException(status_code=400, detail={"code": "SOCIAL_AUTH_ALREADY_LINKED", "message": "이미 연결된 계정입니다"})
        
        db.add(SocialAuth(user_id=db_user.id, provider=request.provider, provider_user_id=val_data["provider_user_id"], email=request.email))
        db.commit()
        return TokenResponse(access_token=create_access_token(data={"sub": str(db_user.id)}), refresh_token=create_refresh_token(data={"sub": str(db_user.id)}), is_new_user=False)
    except Exception as e:
        db.rollback()
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail={"code": "REGISTRATION_FAILED", "message": f"An unexpected error occurred: {str(e)}"})
