from pydantic import BaseModel, Field
from typing import Optional

class SocialLoginRequest(BaseModel):
    provider: str = Field(..., description="소셜 플랫폼 이름 (예: kakao, google)")
    provided_token: str = Field(..., description="프론트엔드에서 발급받은 소셜 액세스 토큰")

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    is_new_user: bool = False
    provider_user_id: Optional[str] = None
    provider: Optional[str] = None
    email: Optional[str] = None