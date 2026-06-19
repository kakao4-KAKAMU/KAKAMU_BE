from uuid import UUID
from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, func

from app.models.user import User, LocalAuth, SocialAuth
from app.schemas.request.auth import SocialLinkRequest, LocalLinkRequest
from app.schemas.response.auth import AccountSettingsResponse, LocalAuthStatus, SocialAuthStatus
from app.service.user.social_auth import get_kakao_user_info
from app.core.security import get_password_hash

SUPPORTED_PROVIDERS = ["kakao", "google"]

class AuthLinkService:
    
    @staticmethod
    def get_account_status(db: Session, user: User) -> AccountSettingsResponse:
        """
        현재 유저의 로컬(이메일) 및 소셜 연동 상태를 계산하여 반환합니다.
        """
        # 1. 로컬 계정 정보 조회
        local_auth = db.scalar(select(LocalAuth).where(LocalAuth.user_id == user.id))
        local_status = LocalAuthStatus(
            is_linked=bool(local_auth),
            email=local_auth.email if local_auth else None
        )
        
        # 2. 소셜 계정 정보 조회
        social_auths = db.scalars(select(SocialAuth).where(SocialAuth.user_id == user.id)).all()
        linked_providers = {sa.provider: sa for sa in social_auths}
        
        social_status_list = []
        earliest_social_time = None
        earliest_social_provider = None

        for provider in SUPPORTED_PROVIDERS:
            sa = linked_providers.get(provider)
            if sa:
                social_status_list.append(SocialAuthStatus(
                    provider=provider, is_linked=True, connected_at=sa.connected_at, email=sa.email
                ))
                if not earliest_social_time or sa.connected_at < earliest_social_time:
                    earliest_social_time = sa.connected_at
                    earliest_social_provider = sa.provider
            else:
                social_status_list.append(SocialAuthStatus(provider=provider, is_linked=False))

        # 3. 주(Primary) 가입 수단 결정 로직 (최초 가입 기준)
        primary_provider = "local"
        if local_auth:
            # 로컬과 소셜이 둘 다 있다면, 유저 생성일과 소셜 연동일을 비교하여 가입 수단 판단
            if earliest_social_time and earliest_social_time < user.created_at:
                primary_provider = earliest_social_provider
        else:
            primary_provider = earliest_social_provider or "unknown"

        return AccountSettingsResponse(
            primary_provider=primary_provider,
            local_auth=local_status,
            social_auths=social_status_list
        )

    @staticmethod
    async def link_social_account(db: Session, user_id: UUID, request: SocialLinkRequest) -> None:
        """소셜 계정을 현재 유저에 연동합니다."""
        if request.provider not in SUPPORTED_PROVIDERS:
            raise HTTPException(status_code=400, detail={"code": "UNSUPPORTED_PROVIDER", "message": "지원하지 않는 소셜 플랫폼입니다."})
            
        # 1. 소셜 프로바이더로부터 유저 정보 가져오기
        if request.provider == "kakao":
            user_info = await get_kakao_user_info(request.provided_token)
            provider_user_id = str(user_info.get("id"))
            email = user_info.get("kakao_account", {}).get("email")
        else:
            raise HTTPException(status_code=400, detail={"code": "UNSUPPORTED_PROVIDER", "message": "해당 플랫폼의 연동은 아직 지원하지 않습니다."})

        # 2. 예외 처리: 이미 내 계정에 해당 프로바이더가 연동되어 있는지 확인
        existing_my_link = db.scalar(select(SocialAuth).where(and_(SocialAuth.user_id == user_id, SocialAuth.provider == request.provider)))
        if existing_my_link:
            raise HTTPException(status_code=400, detail={"code": "SOCIAL_AUTH_ALREADY_LINKED", "message": "이미 연동된 소셜 계정입니다."})

        # 3. 예외 처리: 이 소셜 계정이 다른 유저에게 이미 연동되어 있는지 확인 (Unique 제약조건 방어)
        existing_other_link = db.scalar(select(SocialAuth).where(and_(SocialAuth.provider == request.provider, SocialAuth.provider_user_id == provider_user_id)))
        if existing_other_link:
            raise HTTPException(status_code=400, detail={"code": "SOCIAL_ACCOUNT_ALREADY_USED", "message": "이 소셜 계정은 이미 다른 사용자와 연동되어 있습니다."})

        # 4. 연동 정보 저장
        new_social_auth = SocialAuth(
            user_id=user_id,
            provider=request.provider,
            provider_user_id=provider_user_id,
            email=email
        )
        db.add(new_social_auth)
        db.commit()

    @staticmethod
    def link_local_account(db: Session, user_id: UUID, request: LocalLinkRequest) -> None:
        """이메일/비밀번호(LocalAuth) 로그인 수단을 추가 연동합니다."""
        # 1. 이미 로컬 연동이 되어있는지 확인
        existing_local = db.scalar(select(LocalAuth).where(LocalAuth.user_id == user_id))
        if existing_local:
            raise HTTPException(status_code=400, detail={"code": "LOCAL_AUTH_ALREADY_LINKED", "message": "이미 이메일 계정이 연동되어 있습니다."})
        
        # 2. 연동할 이메일 결정 (입력하지 않은 경우 소셜 계정의 이메일 사용)
        email = request.email
        if not email:
            social_auth = db.scalar(select(SocialAuth).where(and_(SocialAuth.user_id == user_id, SocialAuth.email.isnot(None))))
            if not social_auth:
                raise HTTPException(status_code=400, detail={"code": "EMAIL_REQUIRED", "message": "소셜 계정에 이메일 정보가 없어 이메일을 직접 입력해야 합니다."})
            email = social_auth.email
            
        # 3. 이메일 중복 사용 검증
        email_conflict = db.scalar(select(LocalAuth).where(LocalAuth.email == email))
        if email_conflict:
            raise HTTPException(status_code=400, detail={"code": "EMAIL_ALREADY_USED", "message": "이미 다른 계정에서 사용 중인 이메일입니다."})
            
        # 4. 로컬 로그인 수단 추가
        new_local_auth = LocalAuth(
            user_id=user_id,
            email=email,
            password_hash=get_password_hash(request.password),
            email_verified=1  # 소셜 로그인 또는 로그인 상태이므로 이메일 인증이 된 것으로 간주
        )
        db.add(new_local_auth)
        db.commit()

    @staticmethod
    def unlink_social_account(db: Session, user_id: UUID, provider: str) -> None:
        """소셜 계정 연동을 해제합니다."""
        social_auth = db.scalar(select(SocialAuth).where(and_(SocialAuth.user_id == user_id, SocialAuth.provider == provider)))
        if not social_auth:
            raise HTTPException(status_code=404, detail={"code": "SOCIAL_AUTH_NOT_FOUND", "message": "해당 소셜 계정이 연동되어 있지 않습니다."})

        # 예외 처리: 유일한 로그인 수단인 경우 해제 방지
        local_count = db.scalar(select(func.count(LocalAuth.auth_id)).where(LocalAuth.user_id == user_id))
        social_count = db.scalar(select(func.count(SocialAuth.social_id)).where(SocialAuth.user_id == user_id))
        
        if local_count == 0 and social_count <= 1:
            raise HTTPException(status_code=400, detail={"code": "CANNOT_UNLINK_ONLY_AUTH", "message": "최소 1개의 로그인 수단은 유지해야 합니다. 다른 계정을 연동한 후 시도해주세요."})

        # 연동 해제 (삭제)
        db.delete(social_auth)
        db.commit()