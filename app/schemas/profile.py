from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from uuid import UUID

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
    id: UUID
    user_id: UUID
    nickname: str
    tag: str
    profile_msg: Optional[str] = None
    persona_type: str
#     persona_type: Optional[str] = None
#     is_main: int
#     preference_status: Optional[str] = None
    profile_image_url: str

    model_config = ConfigDict(from_attributes=True)

# 페르소나 수정
class PersonaEdit(BaseModel):
    nickname: Optional[str] = None
    persona_type: Optional[str] = None
    profile_image_url: Optional[str] = None
    profile_msg: Optional[str] = None
