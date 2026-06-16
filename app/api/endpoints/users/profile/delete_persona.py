from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.api.deps import get_active_user
from app.db.session import get_db
from app.models import User
from app.service.profile.delete_persona import PersonaDeleteService
from app.schemas.errors import (
    ERROR_MINIMUM_PERSONA_REQUIRED,
    ERROR_PERSONA_NOT_FOUND,
    ERROR_PERSONA_DELETE_FAILED
)

router = APIRouter()

@router.delete(
    "/personas/{persona_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        400: ERROR_MINIMUM_PERSONA_REQUIRED,
        404: ERROR_PERSONA_NOT_FOUND,
        500: ERROR_PERSONA_DELETE_FAILED
    },
    summary="페르소나 즉시 삭제"
)
async def delete_persona(
    persona_id: UUID,
    user: User = Depends(get_active_user),
    db: Session = Depends(get_db)
):
    """
    특정 페르소나를 즉시 삭제합니다.
    최소 1개의 활성 페르소나가 유지되어야 합니다.
    """
    await PersonaDeleteService.delete_persona(
        db=db,
        user_id=user.id,
        persona_id=persona_id
    )
