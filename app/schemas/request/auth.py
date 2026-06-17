from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from app.schemas.request.common import NotEmptyStr, PasswordStr

class LocalLoginRequest(BaseModel):
    email: EmailStr = Field(..., description="로그인에 사용할 이메일")
    password: str = Field(..., description="비밀번호")

class SocialLoginRequest(BaseModel):
    provider: str = Field(..., description="소셜 플랫폼 이름 (예: kakao, google)")
    provided_token: str = Field(..., description="프론트엔드에서 발급받은 소셜 액세스 토큰")

class RefreshRequest(BaseModel):
    refresh_token: str

class UserRegister(BaseModel):
    username: NotEmptyStr = Field(..., min_length=2, max_length=50, description="사용자 실명 (2~50자)")
    nickname: NotEmptyStr = Field(..., min_length=2, max_length=50, description="서비스 내 닉네임 (2~50자)")
    firebase_id_token: str = Field(..., description="Firebase 번호 인증 완료 시 발급된 ID 토큰")
    email: EmailStr = Field(..., description="로그인에 사용할 이메일")
    password: PasswordStr = Field(..., min_length=8, description="비밀번호는 최소 8자 이상이어야 합니다.")

class LocalLinkRequest(BaseModel):
    email: Optional[EmailStr] = Field(default=None, description="연동할 이메일 (미입력 시 소셜 계정의 이메일 자동 사용)")
    password: PasswordStr = Field(..., min_length=8, description="연동할 비밀번호")

class SocialRegisterRequest(BaseModel):
    provider: str = Field(..., description="소셜 플랫폼 이름 (예: kakao)")
    provided_token: str = Field(..., description="소셜 로그인 성공 시 발급받은 액세스 토큰")
    username: NotEmptyStr = Field(..., min_length=2, max_length=50, description="사용자 실명")
    nickname: NotEmptyStr = Field(..., min_length=2, max_length=50, description="서비스 내 닉네임")
    firebase_id_token: str = Field(..., description="Firebase 번호 인증 완료 시 발급된 ID 토큰")
    email: Optional[EmailStr] = Field(default=None, description="소셜 계정에 연동된 이메일 (선택 동의 시)")

class SocialLinkRequest(BaseModel):
    provider: str = Field(..., description="소셜 플랫폼 이름 (예: kakao)")
    provided_token: str = Field(..., description="소셜 로그인 성공 시 발급받은 액세스 토큰")
    email: Optional[EmailStr] = Field(default=None, description="소셜 계정에 연동된 이메일 (선택 동의 시)")

class PhoneVerificationRequest(BaseModel):
    email: EmailStr = Field(..., description="가입 시 사용한 이메일")
    firebase_id_token: str = Field(..., description="Firebase 번호 인증 완료 시 발급된 ID 토큰")

class PasswordResetRequest(BaseModel):
    email: EmailStr = Field(..., description="가입 시 사용한 이메일")
    firebase_id_token: str = Field(..., description="Firebase 번호 인증 완료 시 발급된 ID 토큰")
    new_password: PasswordStr = Field(..., min_length=8, description="새로운 비밀번호")