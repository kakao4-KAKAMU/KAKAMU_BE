from pydantic import BaseModel, EmailStr, Field, field_validator
import re

class PasswordResetRequest(BaseModel):
    email: EmailStr = Field(..., description="가입 시 사용한 이메일")
    firebase_id_token: str = Field(..., description="Firebase 번호 인증 완료 시 발급된 ID 토큰")
    new_password: str = Field(..., min_length=8, description="새로운 비밀번호")

    @field_validator('new_password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not re.match(r'^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d@$!%*#?&]{8,}$', v):
            raise ValueError("비밀번호는 영문, 숫자를 포함해야 합니다.")
        return v