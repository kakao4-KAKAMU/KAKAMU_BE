from pydantic import BaseModel, EmailStr, Field, field_validator
import re
from typing import Optional

class LocalLinkRequest(BaseModel):
    email: Optional[EmailStr] = Field(default=None, description="연동할 이메일 (미입력 시 소셜 계정의 이메일 자동 사용)")
    password: str = Field(..., min_length=8, description="연동할 비밀번호")

class UserRegister(BaseModel):
    username: str = Field(..., min_length=2, max_length=50, description="사용자 실명 (2~50자)")
    nickname: str = Field(..., min_length=2, max_length=50, description="서비스 내 닉네임 (2~50자)")
    firebase_id_token: str = Field(..., description="Firebase 번호 인증 완료 시 발급된 ID 토큰")
    email: EmailStr = Field(..., description="로그인에 사용할 이메일")
    password: str = Field(..., min_length=8, description="비밀번호는 최소 8자 이상이어야 합니다.")

    @field_validator('username', 'nickname')
    @classmethod
    def strip_and_check_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("공백으로만 이루어질 수 없습니다.")
        return v
        
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not re.match(r'^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!%*#?&]{8,}$', v):
            raise ValueError("비밀번호는 영문, 숫자, 특수문자를 포함해야 합니다.")
        return v