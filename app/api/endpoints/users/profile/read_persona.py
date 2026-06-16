from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_active_user, get_current_persona
from app.db.session import get_db
from app.models import User
from app.schemas.response.profile import PersonaResponse
from app.service.profile import PersonaService
from app.schemas.errors import ERROR_PERSONA_NOT_FOUND

router = APIRouter()


# 모든 페르소나 조회
@router.get(
    "/personas",
    response_model=List[PersonaResponse],
    summary="내 페르소나 목록 전체 조회"
)
async def get_my_personas(
    user: User = Depends(get_active_user),
    db: Session = Depends(get_db)
):
    return await PersonaService.get_my_personas(
        db=db,
        user_id=user.id
    )

# 특정 페르소나만 조회
@router.get(
    "/personas/{persona_id}",
    response_model=PersonaResponse,
    responses={
        404: ERROR_PERSONA_NOT_FOUND
    },
    summary="단일 페르소나 상세 조회"
)
async def get_persona_detail(
    persona_id: UUID,
    user: User = Depends(get_active_user),
    db: Session = Depends(get_db)
):
    return await PersonaService.get_persona_detail(
        db=db,
        user_id=user.id,
        persona_id=persona_id
    )