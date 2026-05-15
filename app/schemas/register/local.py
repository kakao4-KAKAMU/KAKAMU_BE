from pydantic import BaseModel, EmailStr, Field

class UserRegister(BaseModel):
    username: str = Field(..., min_length=2, max_length=50, description="사용자 실명 (2~50자)")
    nickname: str = Field(..., min_length=2, max_length=50, description="서비스 내 닉네임 (2~50자)")
    firebase_id_token: str = Field(..., description="Firebase 번호 인증 완료 시 발급된 ID 토큰")
    email: EmailStr = Field(..., description="로그인에 사용할 이메일")
    password: str = Field(..., min_length=8, description="비밀번호는 최소 8자 이상이어야 합니다.")