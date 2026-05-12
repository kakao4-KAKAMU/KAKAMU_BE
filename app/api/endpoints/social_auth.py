from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.social_auth import SocialLoginRequest, TokenResponse, SocialRegisterRequest
from app.service.social_auth import get_kakao_user_info, get_kakao_access_token
from app.models.models import User, SocialAuth
from app.core.security import create_access_token
from app.core.config import settings

router = APIRouter()

@router.post("/login", response_model=TokenResponse)
async def social_login(request: SocialLoginRequest, db: Session = Depends(get_db)):
    """소셜 토큰을 검증하고, 기존 회원이면 JWT 발급, 신규 회원이면 회원가입 유도 응답을 보냅니다."""
    try:
        if request.provider == "kakao":
            # 1. 프론트엔드에서 '인가 코드(code)'를 보낸 경우 (REST API 방식)
            if request.code:
                if not settings.KAKAO_REST_API_KEY:
                    raise HTTPException(status_code=500, detail={"code": "KAKAO_API_KEY_NOT_SET", "message": "카카오 API 키가 서버에 설정되지 않았습니다."})
                access_token = await get_kakao_access_token(
                    auth_code=request.code,
                    rest_api_key=settings.KAKAO_REST_API_KEY,
                    redirect_uri=request.redirect_uri
                )
            # 2. 프론트엔드에서 '액세스 토큰(token)'을 바로 보낸 경우 (JS SDK 방식 등)
            elif request.token:
                access_token = request.token
            else:
                raise HTTPException(status_code=400, detail={"code": "TOKEN_OR_CODE_REQUIRED", "message": "토큰 또는 인가 코드가 필요합니다."})
                
            user_info = await get_kakao_user_info(access_token)
            provider_user_id = str(user_info.get("id"))
            email = user_info.get("kakao_account", {}).get("email")
        else:
            raise HTTPException(status_code=400, detail={"code": "UNSUPPORTED_SOCIAL_PROVIDER", "message": "지원하지 않는 소셜 플랫폼입니다."})
            
        # 기존 소셜 연동 내역 확인
        social_auth = db.query(SocialAuth).filter(
            SocialAuth.provider == request.provider,
            SocialAuth.provider_user_id == provider_user_id
        ).first()
        
        if social_auth:
            # 기존 회원 -> 바로 JWT 발급
            access_token = create_access_token(data={"sub": str(social_auth.user_id)})
            return TokenResponse(access_token=access_token, is_new_user=False)
        else:
            # 신규 회원 -> 추가 정보 입력 단계로 넘어가도록 처리
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

@router.post("/register", response_model=TokenResponse)
def social_register(request: SocialRegisterRequest, db: Session = Depends(get_db)):
    """추가 정보를 받아 User와 SocialAuth를 생성하고 JWT를 발급합니다."""
    try:
        # 1. 중복 체크
        if db.query(User).filter(User.phone == request.phone).first():
            raise HTTPException(status_code=400, detail={"code": "DUPLICATE_PHONE_NUMBER", "message": "이미 가입된 전화번호입니다."})
        if db.query(User).filter(User.ci_value == request.ci_value).first():
            raise HTTPException(status_code=400, detail={"code": "DUPLICATE_CI_VALUE", "message": "이미 가입된 본인인증 정보입니다."})
            
        # 2. User 테이블 생성
        new_user = User(
            username=request.username,
            nickname=request.nickname,
            phone=request.phone,
            ci_value=request.ci_value
        )
        db.add(new_user)
        db.flush() # new_user의 id를 얻기 위해 flush
        
        # 3. SocialAuth 테이블 연동 정보 생성
        new_social = SocialAuth(
            user_id=new_user.id,
            provider=request.provider,
            provider_user_id=request.provider_user_id,
            email=request.email
        )
        db.add(new_social)
        
        db.commit()
        
        # 4. JWT 토큰 발급
        access_token = create_access_token(data={"sub": str(new_user.id)})
        return TokenResponse(access_token=access_token, is_new_user=False)
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"Social Register Error: {str(e)}")
        raise HTTPException(status_code=500, detail={"code": "REGISTRATION_FAILED", "message": f"An unexpected error occurred: {str(e)}"})