from pydantic import BaseModel
from typing import Optional

class SocialLoginRequest(BaseModel):
    provider: str  # 예: "kakao", "google", "apple"
    # JS SDK를 쓰면 token을 바로 받고, REST API 방식을 쓰면 code를 받습니다.
    token: Optional[str] = None
    code: Optional[str] = None
    redirect_uri: Optional[str] = None

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    is_new_user: bool = False
    provider_user_id: Optional[str] = None
    provider: Optional[str] = None
    email: Optional[str] = None

class SocialRegisterRequest(BaseModel):
    provider: str
    provider_user_id: str
    # User 테이블의 필수(nullable=False) 값들
    username: str
    nickname: str
    phone: str
    email: Optional[str] = None
    ci_value: str