from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class UserAccount(BaseModel):
    id: UUID
    username: str = Field(..., max_length=50)
    nickname: str = Field(..., max_length=50)
    phone: str = Field(..., max_length=20)
    tag: str
    profile_image_url: Optional[str] = None
    profile_msg: Optional[str] = None
    created_at: datetime


class UserSimple(BaseModel):
    id: Optional[UUID] = None
    nickname: str
    tag: str
    profile_image: Optional[str] = None
    profile_msg: Optional[str] = None
    created_at: datetime

class UserSimpleWithFollow(UserSimple):
    is_following: bool


class UserPublic(UserSimpleWithFollow):
    follower_count: Optional[int] = 0
    following_count: Optional[int] = 0
    post_count: Optional[int] = 0

