from pydantic import BaseModel, ConfigDict, EmailStr, Field
from datetime import datetime
from uuid import UUID
from typing import Optional

class UserBase(BaseModel):
    username: str = Field(..., max_length=50)
    nickname: str = Field(..., max_length=50)
    phone: str = Field(..., max_length=20)

class UserResponse(UserBase):
    id: UUID
    tag: str
    profile_image_url: Optional[str] = None
    profile_msg: Optional[str] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class UserUpdate(BaseModel):
    nickname: Optional[str] = Field(None, max_length=50, description="수정할 닉네임")
    profile_image_url: Optional[str] = Field(None, max_length=500, description="수정할 프로필 이미지 URL")
