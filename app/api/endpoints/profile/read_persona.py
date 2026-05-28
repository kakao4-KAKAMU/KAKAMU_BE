from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import User
from app.schemas.profile import PersonaResponse
from app.service.profile import PersonaService

router = APIRouter()


# 모든 페르소나 조회
@router.get("/personas", response_model=List[PersonaResponse])
async def get_my_personas(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return await PersonaService.get_my_personas(
        db=db,
        user_id=user.id
    )

# 특정 페르소나만 조회
@router.get("/personas/{persona_id}", response_model=PersonaResponse)
async def get_persona_detail(
    persona_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return await PersonaService.get_persona_detail(
        db=db,
        user_id=user.id,
        persona_id=persona_id
    )