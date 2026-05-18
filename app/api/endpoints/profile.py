import string
from http.client import HTTPException

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.models import Persona
from app.schemas.profile import UserWithProfileResponse
from app.service import profile as profile_service
from pydantic import BaseModel
import re
router = APIRouter()

# 프론트엔드로부터 오는 데이터 형식 검사
class PersonaCreate(BaseModel):
    nickname: str # 닉네임
    persona_type: str # 좋아하는 장르, 영화 배우
    proflie_image_url: str # 이미지 url, 기본 프로필 이미지 url 필요
    profile_msg: str = ""

@router.post("/new_persona")
def new_persona_proflie(
        persona_data: PersonaCreate, # 사용자 입력 데이터
        user: dict = Depends(get_current_user), # 현재 액세스 토큰으로 인증된 user 정보
        db: Session = Depends(get_db),
):
    if '#' not in persona_data.nickname:
        raise HTTPException(
            status_code=400,
            detail="닉네임 형식이 틀립니다. '닉네임#태그' 형태로 입력하세요. "
        )

    name, tag = persona_data.nickname.split('#', 1)

    if not re.fullmatch(r'[A-Za-z0-9]{3,5}', tag):
        raise HTTPException(
            status_code=400,
            detail="태그 형식이 틀립니다. 태그는 숫자와 영어만 가능하며 3~5글자여야 합니다."
        )

    try:
        new_profile = Persona(
            user_id = user.id,
            nickname = name,
            profile_msg = persona_data.profile_msg,
            persona_type = persona_data.persona_type,
            is_main = 1,
            preference_status = "on",
            tag=tag,
            proflie_image_url = persona_data.proflie_image_url,
            status = "ACTIVIE",
            delete_at = None
        )

        db.add(new_profile)
        db.commit()
        db.refresh(new_profile)

        return {"message": "페르소나 생성 완료"}
    except Exception as e:
        db.rollback()

    new_profile = Persona(user.id,name,profile_msg,persona_type,1,"select",tag,profile_image_url,"ACTIVIE",Nu)




@router.get("/{user_id}", response_model=UserWithProfileResponse)
def read_user_profile(user_id: int, db: Session = Depends(get_db)):
    """
    ### 1. 프로필 조회
    - trd특정 사용자의 기본 정보와 생성된 페르소나(프로필) 목록을 함께 조회합니다.
    """
    return profile_service.get_user_with_profiles(db=db, user_id=user_id)