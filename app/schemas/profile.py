from pydantic import BaseModel, ConfigDict, field_serializer
from typing import List, Optional
from uuid import UUID

from app.core.config import settings


# 페르소나 프로필 생성
class PersonaCreate(BaseModel):
    nickname: str # 닉네임
    # persona_type: str # 별도 테이블 fav_genre, fav_movie, fav_people, 삭제 필요
    profile_image_url: Optional[str] = None # 이미지 url, 기본 프로필 이미지 url 필요
    profile_msg: str = ""
    
    fav_movie_ids: Optional[List[int]] = None # 선호 영화 ID 목록
    fav_genre_ids: Optional[List[int]] = None # 선호 장르 ID 목록
    fav_people_ids: Optional[List[int]] = None # 선호 인물(배우/감독) ID 목록


# 개별 프로필(페르소나) 정보
class PersonaResponse(BaseModel):
    id: UUID # 페르소나 id
    user_id: UUID # 유저 id
    nickname: str # 닉네임
    tag: str # 태그
    profile_msg: Optional[str] = None # 프로필 메시지
    # persona_type: str
#     persona_type: Optional[str] = None
    profile_image_url: str # 이미지 경로

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

# 페르소나 수정
class PersonaEdit(BaseModel):
    nickname: Optional[str] = None
    # persona_type: Optional[str] = None # 삭제 필요
    profile_image_url: Optional[str] = None
    profile_msg: Optional[str] = None

    fav_movie_ids: Optional[List[int]] = None # 선호 영화 ID 목록
    fav_genre_ids: Optional[List[int]] = None # 선호 장르 ID 목록
    fav_people_ids: Optional[List[int]] = None # 선호 인물(배우/감독) ID 목록
