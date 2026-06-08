from pydantic import BaseModel, ConfigDict, field_serializer
from typing import Optional
from uuid import UUID
from app.core.config import settings

# 개별 프로필(페르소나) 정보
class PersonaResponse(BaseModel):
    id: UUID # 페르소나 id
    user_id: UUID # 유저 id
    nickname: str # 닉네임
    profile_image_url: Optional[str] = None # 이미지 경로
    is_following: Optional[bool] = False # 팔로우 상태 필드 추가
    follower_count: Optional[int] = 0
    following_count: Optional[int] = 0
    post_count: Optional[int] = 0

    @field_serializer("profile_image_url")
    def serialize_profile_image_url(self, value: str):
        if not value:
            return value
        if value.startswith("http://") or value.startswith("https://"):
            return value
        if value.startswith("/static"):
            return f"{settings.DEFAULT_IMAGE.rstrip('/')}/{value.lstrip('/')}"
        return f"{settings.IMAGE_SERVER_URL.rstrip('/')}/{value.lstrip('/')}"

    model_config = ConfigDict(from_attributes=True)
