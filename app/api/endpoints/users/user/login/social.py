from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.request.auth import SocialLoginRequest
from app.schemas.response.auth import TokenResponse
from app.service.user.social_auth import get_kakao_user_info
from app.models import SocialAuth, Persona
from app.core.security import create_access_token, create_refresh_token
from app.schemas.errors import (
    ERROR_UNSUPPORTED_SOCIAL_PROVIDER,
    ERROR_LOGIN_UNEXPECTED_ERROR
)

router = APIRouter()

@router.post(
    "/social",
    response_model=TokenResponse,
    responses={400: ERROR_UNSUPPORTED_SOCIAL_PROVIDER, 500: ERROR_LOGIN_UNEXPECTED_ERROR}
)
async def social_login(request: SocialLoginRequest, db: Session = Depends(get_db)):
    """소셜 토큰을 검증하고, 기존 회원이면 JWT 발급, 신규 회원이면 회원가입 유도 응답을 보냅니다."""
    try:
        if request.provider == "kakao":
            user_info = await get_kakao_user_info(request.provided_token)
            provider_user_id = str(user_info.get("id"))
            email = user_info.get("kakao_account", {}).get("email")
        else:
            raise HTTPException(status_code=400, detail={"code": "UNSUPPORTED_SOCIAL_PROVIDER", "message": "지원하지 않는 소셜 플랫폼입니다."})
            
        social_auth = db.query(SocialAuth).filter(
            SocialAuth.provider == request.provider,
            SocialAuth.provider_user_id == provider_user_id
        ).first()
        
        if social_auth:
            access_token = create_access_token(data={"sub": str(social_auth.user_id), "provider": request.provider})
            refresh_token = create_refresh_token(data={"sub": str(social_auth.user_id), "provider": request.provider})
            return TokenResponse(access_token=access_token, refresh_token=refresh_token, is_new_user=False)
        else:
            return TokenResponse(
                access_token="",
                is_new_user=True,
                provider_user_id=provider_user_id,
                provider=request.provider,
                email=email
            )
    except HTTPException:
        raise
    except Exception as e:
        print(f"Social Login Error: {str(e)}")
        raise HTTPException(status_code=500, detail={"code": "LOGIN_UNEXPECTED_ERROR", "message": f"An unexpected error occurred: {str(e)}"})