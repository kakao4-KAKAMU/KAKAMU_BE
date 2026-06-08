from pydantic import BaseModel, Field
from typing import Optional

class UserUpdate(BaseModel):
    nickname: Optional[str] = Field(None, max_length=50, description="수정할 닉네임")
    profile_image_url: Optional[str] = Field(None, max_length=500, description="수정할 프로필 이미지 URL")
