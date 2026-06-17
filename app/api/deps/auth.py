from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import select
import jwt
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError
from typing import Optional

from app.core.config import settings
from app.db.session import get_db
from app.models import User

security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)) -> User:
    access_token = credentials.credentials
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={"code": "INVALID_CREDENTIALS", "message": "Could not validate credentials"},
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(access_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        
        # 리프레시 토큰이 액세스 토큰 자리에 사용되는 것을 차단 (Token Substitution 방어)
        if payload.get("type") == "refresh":
            raise credentials_exception
            
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "TOKEN_EXPIRED", "message": "액세스 토큰이 만료되었습니다. 토큰을 재발급 받아주세요."},
            headers={"WWW-Authenticate": "Bearer"},
        )
    except InvalidTokenError:
        raise credentials_exception
        
    user = db.scalar(select(User).where(User.id == user_id))
    if user is None:
        raise credentials_exception
    return user

def get_active_user(current_user: User = Depends(get_current_user)) -> User:
    """
    일반적인 서비스 API 호출 시 사용되는 의존성입니다.
    현재 로그인한 유저가 탈퇴 유예 기간(DELETED)인 경우 접근을 403으로 차단합니다.
    """
    if current_user.status == "DELETED":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "ACCOUNT_IN_GRACE_PERIOD", "message": "탈퇴 유예 기간 중인 계정입니다. 서비스 이용을 위해 계정을 복구해주세요."}
        )
        
    return current_user

def get_optional_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)) -> Optional[User]:
    """
    비회원(로그인하지 않은 유저)도 접근 가능한 API를 위한 선택적 인증 의존성입니다.
    토큰이 없거나 유효하지 않으면 에러를 띄우지 않고 None을 반환합니다.
    """
    if not credentials:
        return None
    try:
        payload = jwt.decode(credentials.credentials, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("type") == "refresh":
            return None
        user = db.scalar(select(User).where(User.id == payload.get("sub"), User.status == "ACTIVE"))
        return user
    except Exception:
        return None