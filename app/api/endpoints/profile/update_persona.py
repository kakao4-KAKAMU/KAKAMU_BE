import redis
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.schemas.profile import PersonaEdit, PersonaResponse
from app.models.models import User
from app.service.profile import PersonaService
from app.core.redis import get_redis

router = APIRouter()

@router.patch("/persona/{persona_id}")
async def edit_persona_profile(
        persona_id: int,
        persona_edit_data: PersonaEdit,
        user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
        redis_client = Depends(get_redis)
):
    return await PersonaService.update_persona(db=db, redis_client=redis_client, persona_id=persona_id,edit_data=persona_edit_data,user_id=user.id)

@router.patch("/personas/{persona_id}/activate", response_model=PersonaResponse)
async def activate_persona(
    persona_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis)
):
    return await PersonaService.activate_persona(
        db=db,
        redis_client=redis_client,
        user_id=user.id,
        persona_id=persona_id
    )