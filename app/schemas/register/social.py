from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class SocialRegisterRequest(BaseModel):
    """소셜 회원가입 시 프론트엔드로부터 전달받는 데이터 스키마입니다."""
    provider: str = Field(..., description="소셜 플랫폼 이름 (예: kakao)")
    provided_token: str = Field(..., description="소셜 로그인 성공 시 발급받은 액세스 토큰")
    username: str = Field(..., min_length=2, max_length=50, description="사용자 실명")
    nickname: str = Field(..., min_length=2, max_length=50, description="서비스 내 닉네임")
    phone: str = Field(..., min_length=10, max_length=20, description="전화번호 (010... 형태)")
    email: Optional[EmailStr] = Field(default=None, description="소셜 계정에 연동된 이메일 (선택 동의 시)")