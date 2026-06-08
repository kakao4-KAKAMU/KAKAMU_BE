from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_active_user, get_current_persona
from app.db.session import get_db
from app.models import User
from app.schemas.response.profile import PersonaResponse
from app.service.profile import PersonaService

router = APIRouter()


# 모든 페르소나 조회
@router.get("/personas", response_model=List[PersonaResponse])
async def get_my_personas(
    user: User = Depends(get_active_user),
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
    user: User = Depends(get_active_user),
    db: Session = Depends(get_db)
):
    return await PersonaService.get_persona_detail(
        db=db,
        user_id=user.id,
        persona_id=persona_id
    )

# 타인의 공개 프로필(페르소나) 조회
@router.get("/public/{target_persona_id}", response_model=PersonaResponse)
async def get_public_profile(
    target_persona_id: UUID,
    viewer_persona_id: UUID = Depends(get_current_persona),
    db: Session = Depends(get_db)
):
    return await PersonaService.get_public_persona_profile(
        db=db,
        target_persona_id=target_persona_id,
        viewer_persona_id=viewer_persona_id
    )