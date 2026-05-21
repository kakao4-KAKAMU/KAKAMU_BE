from pydantic import BaseModel, ConfigDict
from typing import List, Optional

# 페르소나 프로필 생성
class PersonaCreate(BaseModel):
    nickname: str # 닉네임
    persona_type: str # 좋아하는 장르, 영화 배우
    profile_image_url: Optional[str] = None # 이미지 url, 기본 프로필 이미지 url 필요
    profile_msg: str = ""


# 개별 프로필(페르소나) 정보
class PersonaResponse(BaseModel):
    id: int
    user_id: int
    nickname: str
    tag: str
    profile_msg: Optional[str] = None
    persona_type: str
    is_main: int
    preference_status: str
    profile_image_url: str

    model_config = ConfigDict(from_attributes=True)

# 페르소나 수정
class PersonaEdit(BaseModel):
    nickname: Optional[str] = None
    persona_type: Optional[str] = None
    profile_image_url: Optional[str] = None
    profile_msg: Optional[str] = None
