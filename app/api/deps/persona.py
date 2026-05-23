from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from uuid import UUID
import jwt

from app.core.config import settings
from app.db.session import get_db

security = HTTPBearer()

async def get_current_persona(
        credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    JWT 토큰의 페이로드에서 persona_id를 추출하여 반환하는 공통 의존성
    """
    try:
        payload = jwt.decode(credentials.credentials, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        persona_id_str = payload.get("persona_id")
        if not persona_id_str:
            raise HTTPException(status_code=400, detail="토큰에 선택된 페르소나 정보가 없습니다. 페르소나 전환 API를 호출해주세요.")
        return UUID(persona_id_str)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="토큰이 만료되었습니다.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="유효하지 않은 토큰입니다.")