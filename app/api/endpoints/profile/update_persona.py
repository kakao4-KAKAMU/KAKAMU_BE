from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.deps import get_active_user
from app.db.session import get_db
from app.models import User
from app.schemas.request.profile import PersonaEdit
from app.schemas.response.profile import PersonaResponse
from app.service.profile.update_persona import PersonaUpdateService

router = APIRouter()

@router.put("/personas/{persona_id}", response_model=PersonaResponse)
async def update_persona(
    persona_id: UUID,
    request: PersonaEdit,
    user: User = Depends(get_active_user),
    db: Session = Depends(get_db)
):
    """
    기존 페르소나의 정보(닉네임, 프로필 메시지, 취향 등)를 수정합니다.
    """
    return await PersonaUpdateService.update_persona(
        db=db,
        user_id=user.id,
        persona_id=persona_id,
        persona_data=request
    )
