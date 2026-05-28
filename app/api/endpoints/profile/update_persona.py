from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from uuid import UUID

from app.api.deps import get_current_user
from app.db.session import get_db
from app.schemas.profile import PersonaEdit
from app.models import User
from app.service.profile import PersonaService

router = APIRouter()

@router.patch("/persona/{persona_id}")
async def edit_persona_profile(
        persona_id: UUID,
        persona_edit_data: PersonaEdit,
        user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    return await PersonaService.update_persona(db=db, persona_id=persona_id, edit_data=persona_edit_data, user_id=user.id)
