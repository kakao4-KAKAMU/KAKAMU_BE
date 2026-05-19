from pydantic import BaseModel, EmailStr, Field

class LocalLoginRequest(BaseModel):
    email: EmailStr = Field(..., description="로그인에 사용할 이메일")
    password: str = Field(..., description="비밀번호")

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class RefreshRequest(BaseModel):
    refresh_token: str