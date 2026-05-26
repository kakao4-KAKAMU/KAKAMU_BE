import redis
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.models.models import User
from app.api.deps import get_current_user
from app.core.redis import get_redis
from app.db.session import get_db
from app.schemas.profile import PersonaCreate, PersonaResponse

from app.service.profile import PersonaService

router = APIRouter()

@router.delete("/persona/{persona_id}", status_code=204)
async def delete_persona(
    persona_id: UUID

):
    await PersonaService.delete_persona_soft(
        db = db,
        redis_client = redis_client,
        user_id = user.id,
        persona_id = persona_id
    )
    return None
