from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional

class SocialLinkRequest(BaseModel):
    provider: str = Field(..., description="소셜 플랫폼 이름 (예: kakao)")
    provided_token: str = Field(..., description="소셜 로그인 성공 시 발급받은 액세스 토큰")
    email: Optional[EmailStr] = Field(default=None, description="소셜 계정에 연동된 이메일 (선택 동의 시)")

class SocialRegisterRequest(BaseModel):
    """소셜 회원가입 시 프론트엔드로부터 전달받는 데이터 스키마입니다."""
    provider: str = Field(..., description="소셜 플랫폼 이름 (예: kakao)")
    provided_token: str = Field(..., description="소셜 로그인 성공 시 발급받은 액세스 토큰")
    username: str = Field(..., min_length=2, max_length=50, description="사용자 실명")
    nickname: str = Field(..., min_length=2, max_length=50, description="서비스 내 닉네임")
    firebase_id_token: str = Field(..., description="Firebase 번호 인증 완료 시 발급된 ID 토큰")
    email: Optional[EmailStr] = Field(default=None, description="소셜 계정에 연동된 이메일 (선택 동의 시)")

    @field_validator('username', 'nickname')
    @classmethod
    def strip_and_check_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("공백으로만 이루어질 수 없습니다.")
        return v