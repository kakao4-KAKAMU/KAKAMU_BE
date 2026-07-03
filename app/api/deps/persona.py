from fastapi import HTTPException, Depends, Header
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Optional

from app.db.session import get_db
from app.models import Persona, User
from app.api.deps.auth import get_optional_user, get_current_user


async def get_optional_persona(
    x_persona_id: Optional[UUID] = Header(
        default=None, description="현재 활성화된 페르소나 ID"
    ),
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> UUID | None:
    if not x_persona_id:
        return None
    if current_user is None:
        return None
    persona = db.get(Persona, x_persona_id)
    if not persona or persona.user_id != current_user.id or persona.status == "DELETED":
        raise HTTPException(status_code=403, detail={"code": "PERSONA_NOT_FOUND_OR_FORBIDDEN", "message": "요청한 페르소나에 대한 권한이 없거나 존재하지 않습니다."})

    return persona.id

async def get_current_persona(
    x_persona_id: Optional[UUID] = Header(
        default=None, description="현재 활성화된 페르소나 ID"
    ),
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UUID | None:
    """
    1. get_active_user를 통해 로그인된(활성화 상태인) 유저를 검증합니다.
    2. 헤더(X-Persona-Id)로 전달받은 페르소나의 소유권과 상태를 검증합니다.
    """
    # 페르소나 유효성 및 소유권 검증
    if not x_persona_id:
        return None

    persona = db.get(Persona, x_persona_id)
    if not persona or persona.user_id != current_user.id or persona.status == "DELETED":
        raise HTTPException(status_code=403, detail={"code": "PERSONA_NOT_FOUND_OR_FORBIDDEN", "message": "요청한 페르소나에 대한 권한이 없거나 존재하지 않습니다."})

    return persona.id
