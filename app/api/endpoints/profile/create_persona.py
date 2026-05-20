import redis
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.redis import get_redis
from app.db.session import get_db
from app.schemas.profile import PersonaCreate, PersonaResponse
from app.models.models import User

from app.service.profile import PersonaService

router = APIRouter()


@router.post("/persona", response_model=PersonaResponse, status_code=201)
async def new_persona_profile(
        persona_data: PersonaCreate, # 사용자 입력 데이터
        user: User = Depends(get_current_user), # 현재 액세스 토큰으로 인증된 user 정보
        db: Session = Depends(get_db), # db 연결 후 세션 객체
        redis_client : redis.Redis = Depends(get_redis) # redis 연결
):
    return await PersonaService.create_new_persona(db=db,redis_client=redis_client, persona_data=persona_data,user_id=user.id)
