from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.models import User
from app.api.deps import get_current_user
from app.db.session import get_db

from app.service.profile import PersonaService

router = APIRouter()

@router.delete("/persona/{persona_id}", status_code=204)
async def delete_persona(
    persona_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    await PersonaService.delete_persona_soft(
        db = db,
        user_id = user.id,
        persona_id = persona_id
    )
    return None
