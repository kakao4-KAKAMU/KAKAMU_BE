from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.api.deps import get_current_user
from app.db.session import get_db
from app.schemas.profile import PersonaEdit, PersonaResponse
from app.models import User
from app.service.profile import PersonaService
from app.core.redis import get_redis

router = APIRouter()

@router.patch("/persona/{persona_id}")
def edit_persona_profile(
        persona_id: UUID,
        persona_edit_data: PersonaEdit,
        user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    return PersonaService.update_persona(db=db, persona_id=persona_id,edit_data=persona_edit_data,user_id=user.id)

@router.patch("/personas/{persona_id}/activate")
async def switch_persona(
    persona_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return await PersonaService.switch_persona(
        db=db,
        user_id=user.id,
        persona_id=persona_id
    )