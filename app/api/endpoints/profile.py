import redis
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.redis import get_redis
from app.db.session import get_db
from app.schemas.profile import PersonaCreate, PersonaResponse, PersonaEdit

from app.service.persona import PersonaService

router = APIRouter()

@router.post("/local")
def register_local_user():
    raise Exception("여기 실행됨")

@router.post("/new_persona234")
def new_persona_profile2():
    return {"ok": True}
# 페르소나 계정 생성, 엔드포인트 /new_persona, 응답은 PersonaResponse 구조로, 상태 코드는 201

