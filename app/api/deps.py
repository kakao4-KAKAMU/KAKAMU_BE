from fastapi import Depends, Header, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import jwt
from jwt.exceptions import InvalidTokenError

from app.core.config import settings
from app.db.session import get_db
from app.models.models import User
from app.service.persona import persona_service

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except InvalidTokenError:
        raise credentials_exception
        
    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise credentials_exception
    return user

async def get_current_persona(x_user_id: int = Header(...)):
    """
    헤더에서 user_id를 받아 현재 활성화된 페르소나 ID를 반환하는 공통 의존성
    """
    persona_id = await persona_service.get_active_persona_id(x_user_id)
    if not persona_id:
        raise HTTPException(status_code=400, detail="활성화된 페르소나가 없습니다. 페르소나를 선택해주세요.")
    return persona_id
