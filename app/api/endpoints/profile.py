from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.schemas.profile import PersonaCreate, PersonaResponse, PersonaEdit

from app.service.persona import PersonaService

router = APIRouter()

@router.post("/new_persona234")
def new_persona_profile2():
    return {"ok": True}
# 페르소나 계정 생성, 엔드포인트 /new_persona, 응답은 PersonaResponse 구조로, 상태 코드는 201
@router.post("/new_persona", response_model=PersonaResponse, status_code=201)
def new_persona_profile(
        persona_data: PersonaCreate, # 사용자 입력 데이터
        user: dict = Depends(get_current_user), # 현재 액세스 토큰으로 인증된 user 정보
        db: Session = Depends(get_db),
):
    return PersonaService.create_new_persona(db=db, persona_data=persona_data,user_id=user.id)


# 페르소나 수정, 수정된 값만 받게하기
@router.patch("/persona/{persona_id}")
def edit_persona_profile(
        persona_id: int,
        persona_edit_data: PersonaEdit,
        db: Session = Depends(get_db)
):
    return PersonaService.update_persona(db=db, persona_id=persona_id,edit_data=persona_edit_data)


# 페르소나 삭제
