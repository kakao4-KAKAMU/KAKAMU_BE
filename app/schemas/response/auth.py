from typing import Optional

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