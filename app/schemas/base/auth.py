from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    is_new_user: bool = False


class KakaoAccount(BaseModel):
    email: Optional[str] = None


class KakaoUserInfo(BaseModel):
    id: int
    kakao_account: Optional[KakaoAccount] = None


class SocialAuthStatus(BaseModel):
    provider: str
    is_linked: bool
    connected_at: Optional[datetime] = None
    email: Optional[str] = None


class LocalAuthStatus(BaseModel):
    is_linked: bool
    email: Optional[str] = None
