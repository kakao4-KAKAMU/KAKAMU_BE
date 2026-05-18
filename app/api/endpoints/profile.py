import string
from http.client import HTTPException

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select, and_

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.models import Persona
from schemas.profile import PersonaCreate, PersonaResponse, PersonaEdit
from app.service import profile as profile_service
from pydantic import BaseModel
import re
router = APIRouter()

# 엔드포인트 /new_persona, 응답은 PersonaResponse 구조로, 상태 코드는 201
@router.post("/new_persona", response_model=PersonaResponse, status_code=201)
def new_persona_profile(
        persona_data: PersonaCreate, # 사용자 입력 데이터
        user: dict = Depends(get_current_user), # 현재 액세스 토큰으로 인증된 user 정보
        db: Session = Depends(get_db),
):
    # 닉네임 형식 검사 : 닉네임#태그
    if '#' not in persona_data.nickname:
        raise HTTPException(
            status_code=400,
            detail="닉네임 형식이 틀립니다. '닉네임#태그' 형태로 입력하세요. "
        )

    name, tag = persona_data.nickname.split('#', 1)
    # 태그 형식 검사
    if not re.fullmatch(r'[A-Za-z0-9]{3,5}', tag): # 대소문자, 0~9, 3글자에서 5글자
        raise HTTPException(
            status_code=400,
            detail="태그 형식이 틀립니다. 태그는 숫자와 영어만 가능하며 3~5글자여야 합니다."
        )
    # persona 테이블에서 닉네임이 존재하는 지 검사
    exist_stmt = select(Persona).where(
        and_(
            Persona.nickname == name, # and 연산으로 name, tag 비교
            Persona.tag == tag
        )
    )

    existing_persona = db.scalar(exist_stmt)  # 존재하는지 확인, scalar는 없으면 None 반환

    if existing_persona:
        raise HTTPException(
            status_code = 400, # 중복된 닉네임있으면 400 에러 발생
            detail = f"이미 존재하는 닉네임과 태그 조합입니다.({persona_data.nickname})"
        )

    
    try:
        new_profile = Persona(
            user_id = user.id,
            nickname = name,
            profile_msg = persona_data.profile_msg,
            persona_type = persona_data.persona_type,
            is_main = 1,
            preference_status = "on", # 현재 활성화된 페르소나 프로필 (on, off)
            tag=tag,
            proflie_image_url = persona_data.proflie_image_url,
            status = "ACTIVE",
            delete_at = None
        )

        db.add(new_profile)
        db.commit()
        db.refresh(new_profile)

        return new_profile # schemas/profile.py에 정의한
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"데이터베이스 저장 중 오류 발생")

# 고려해야 할 것
# 1. 닉네임과 태그가 중복된 경우
# 2. 두번째 계정을 만들 때 preference_status, is_main 값 설정


