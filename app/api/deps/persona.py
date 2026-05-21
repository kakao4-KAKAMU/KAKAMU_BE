from fastapi import Header, HTTPException, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.service.persona import PersonaService

async def get_current_persona(
        x_user_id: int = Header(...),
        db: Session = Depends(get_db)
):
    """
    헤더에서 user_id를 받아 현재 활성화된 페르소나 ID를 반환하는 공통 의존성
    """
    persona_service = PersonaService()
    persona_id = await persona_service.get_current_active_persona_id(db, x_user_id)
    
    if not persona_id:
        raise HTTPException(status_code=400, detail="활성화된 페르소나가 없습니다. 페르소나를 선택해주세요.")
    return persona_id