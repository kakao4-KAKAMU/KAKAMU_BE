from fastapi import Header, HTTPException
from app.service.persona import persona_service

async def get_current_persona(x_user_id: int = Header(...)):
    """
    헤더에서 user_id를 받아 현재 활성화된 페르소나 ID를 반환하는 공통 의존성
    """
    persona_id = await persona_service.get_active_persona_id(x_user_id)
    if not persona_id:
        raise HTTPException(status_code=400, detail="활성화된 페르소나가 없습니다. 페르소나를 선택해주세요.")
    return persona_id