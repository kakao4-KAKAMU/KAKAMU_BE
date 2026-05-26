from pydantic import BaseModel, ConfigDict, EmailStr, Field
from datetime import datetime
from uuid import UUID

class UserBase(BaseModel):
    username: str = Field(..., max_length=50)
    nickname: str = Field(..., max_length=50)
    phone: str = Field(..., max_length=20)

class UserResponse(UserBase):
    id: UUID
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
