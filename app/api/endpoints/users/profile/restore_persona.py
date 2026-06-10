from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.api.deps import get_active_user
from app.db.session import get_db
from app.models import User
from app.schemas.response.profile import PersonaResponse
from app.service.profile.restore_persona import PersonaRestoreService
from app.schemas.errors import ERROR_PERSONA_NOT_FOUND

router = APIRouter()

@router.post(
    "/personas/{persona_id}/restore",
    response_model=PersonaResponse,
    status_code=status.HTTP_200_OK,
    responses={
        404: ERROR_PERSONA_NOT_FOUND
    }
)
async def restore_persona(
    persona_id: UUID,
    user: User = Depends(get_active_user),
    db: Session = Depends(get_db)
):
    """
    삭제(Soft Delete)된 페르소나를 7일의 유예 기간 내에 다시 활성화(복구)합니다.
    """
    return await PersonaRestoreService.restore_persona(
        db=db,
        user_id=user.id,
        persona_id=persona_id
    )