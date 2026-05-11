from pydantic import BaseModel, ConfigDict
from typing import List, Optional

# 개별 프로필(페르소나) 정보
class ProfileResponse(BaseModel):
    id: int
    user_id: int
    nickname: Optional[str] = None
    profile_msg: Optional[str] = None
    persona_type: Optional[str] = None
    is_main: int

    model_config = ConfigDict(from_attributes=True)

# 프로필 조회 시 반환될 최종 응답 (사용자 정보 + 보유 프로필 목록)
class UserWithProfileResponse(BaseModel):
    id: int
    username: str
    nickname: str # 기본 유저 닉네임
    profiles: List[ProfileResponse] = [] # User 모델의 relationship을 통해 자동 매핑됨

    model_config = ConfigDict(from_attributes=True)