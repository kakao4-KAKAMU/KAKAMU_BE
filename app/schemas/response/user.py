from pydantic import BaseModel, ConfigDict, Field
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

# 타인에게 노출되어도 안전한 공개용 유저 정보 스키마
class UserPublicResponse(BaseModel):
    id: UUID
    nickname: str
    tag: str
    profile_image_url: Optional[str] = None
    profile_msg: Optional[str] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
