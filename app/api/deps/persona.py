from fastapi import HTTPException, Depends, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from uuid import UUID
import jwt

from app.core.config import settings
from app.db.session import get_db
from app.models import Persona

security = HTTPBearer()

async def get_current_persona(
        x_persona_id: UUID = Header(..., description="현재 활성화된 페르소나 ID"),
        credentials: HTTPAuthorizationCredentials = Depends(security),
        db: Session = Depends(get_db)
) -> UUID:
    """
    1. JWT 토큰을 검증하여 로그인한 유저(sub)를 식별합니다.
    2. 헤더(X-Persona-Id)로 전달받은 페르소나의 소유권과 상태를 검증합니다.
    """
    try:
        payload = jwt.decode(credentials.credentials, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id_str = payload.get("sub")
        if not user_id_str:
            raise HTTPException(status_code=401, detail="토큰 내 사용자 정보가 없습니다.")
        user_id = UUID(user_id_str)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="토큰이 만료되었습니다.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="유효하지 않은 토큰입니다.")

    # 페르소나 유효성 및 소유권 검증
    persona = db.get(Persona, x_persona_id)
    if not persona or persona.user_id != user_id or persona.status == "DELETED":
        raise HTTPException(status_code=403, detail="요청한 페르소나에 대한 권한이 없거나 존재하지 않습니다.")
        
    return persona.id