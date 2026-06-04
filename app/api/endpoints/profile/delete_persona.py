from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.api.deps import get_active_user
from app.db.session import get_db
from app.models import User
from app.service.profile.delete_persona import PersonaDeleteService

router = APIRouter()

@router.delete("/personas/{persona_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_persona(
    persona_id: UUID,
    user: User = Depends(get_active_user),
    db: Session = Depends(get_db)
):
    """
    특정 페르소나를 삭제(Soft Delete)합니다.
    최소 1개의 활성 페르소나가 유지되어야 합니다.
    """
    await PersonaDeleteService.delete_persona_soft(
        db=db,
        user_id=user.id,
        persona_id=persona_id
    )
