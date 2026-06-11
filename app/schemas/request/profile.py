from pydantic import BaseModel
from typing import List, Optional

# 페르소나 프로필 생성
class PersonaCreate(BaseModel):
    nickname: str # 닉네임
    profile_image_url: Optional[str] = None # 이미지 url
    
    fav_movie_ids: Optional[List[int]] = None # 선호 영화 ID 목록
    fav_genre_ids: Optional[List[int]] = None # 선호 장르 ID 목록
    fav_people_ids: Optional[List[int]] = None # 선호 인물(배우/감독) ID 목록

# 페르소나 수정
class PersonaEdit(BaseModel):
    nickname: Optional[str] = None
    profile_image_url: Optional[str] = None

    fav_movie_ids: Optional[List[int]] = None # 선호 영화 ID 목록
    fav_genre_ids: Optional[List[int]] = None # 선호 장르 ID 목록
    fav_people_ids: Optional[List[int]] = None # 선호 인물(배우/감독) ID 목록
