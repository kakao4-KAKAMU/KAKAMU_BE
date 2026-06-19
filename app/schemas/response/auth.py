from app.schemas.base.auth import (
    KakaoAccount,
    KakaoUserInfo,
    LocalAuthStatus,
    SocialAuthStatus,
)
from pydantic import BaseModel
from typing import List


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    is_new_user: bool = False


class AccountSettingsResponse(BaseModel):
    primary_provider: str
    local_auth: LocalAuthStatus
    social_auths: List[SocialAuthStatus]

__all__ = [
    "TokenResponse",
    "KakaoAccount",
    "KakaoUserInfo",
    "SocialAuthStatus",
    "LocalAuthStatus",
    "AccountSettingsResponse",
]
