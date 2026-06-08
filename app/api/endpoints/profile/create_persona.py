from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.api.deps import get_active_user
from app.db.session import get_db
from app.models import User
from app.schemas.request.profile import PersonaCreate
from app.schemas.response.profile import PersonaResponse
from app.service.profile.create_persona import PersonaCreateService

router = APIRouter()

@router.post("/personas", response_model=PersonaResponse, status_code=status.HTTP_201_CREATED)
async def create_persona(
    request: PersonaCreate,
    user: User = Depends(get_active_user),
    db: Session = Depends(get_db)
):
    """
    새로운 페르소나를 생성합니다.
    (최대 5개까지 생성 가능하며, 서비스 계층에서 PERSONA_LIMIT_EXCEEDED 에러 처리 필요)
    """
    return await PersonaCreateService.create_new_persona(
        db=db,
        user_id=user.id,
        persona_data=request
    )
