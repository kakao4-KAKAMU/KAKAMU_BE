import json
import time

import jwt
from opentelemetry import trace
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError
from sqlalchemy import select
from sqlalchemy.orm import Session
from typing import Optional

from app.core.config import settings
from app.core.logging import logger
from app.core.redis import sync_redis_client
from app.db.session import get_db
from app.models import User, UserStatus

tracer = trace.get_tracer(__name__)
security = HTTPBearer()


def _get_cached_payload(access_token: str) -> Optional[dict]:
    try:
        cached = sync_redis_client.get(access_token)
        if cached is None:
            return None
        return json.loads(cached)
    except Exception as e:
        logger.warning(f"[Redis Error] Auth payload cache read failed: {e}")
        return None


def _cache_payload(access_token: str, payload: dict) -> None:
    exp = payload.get("exp")
    if exp is None:
        return
    try:
        ttl = max(1, int(exp) - int(time.time()))
        sync_redis_client.setex(access_token, ttl, json.dumps(payload))
    except Exception as e:
        logger.warning(f"[Redis Error] Auth payload cache write failed: {e}")


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)) -> User:
    with tracer.start_as_current_span("auth.get_current_user") as span:
        access_token = credentials.credentials
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_CREDENTIALS", "message": "Could not validate credentials"},
            headers={"WWW-Authenticate": "Bearer"},
        )

        payload = _get_cached_payload(access_token)
        span.set_attribute("auth.cache_hit", payload is not None)

        if payload is None:
            try:
                payload = jwt.decode(access_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
                _cache_payload(access_token, payload)
            except ExpiredSignatureError:
                span.set_attribute("auth.result", "token_expired")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail={"code": "TOKEN_EXPIRED", "message": "액세스 토큰이 만료되었습니다. 토큰을 재발급 받아주세요."},
                    headers={"WWW-Authenticate": "Bearer"},
                )
            except InvalidTokenError:
                span.set_attribute("auth.result", "invalid_token")
                raise credentials_exception

        # 리프레시 토큰이 액세스 토큰 자리에 사용되는 것을 차단 (Token Substitution 방어)
        if payload.get("type") == "refresh":
            span.set_attribute("auth.result", "refresh_token_substitution")
            raise credentials_exception

        user_id: str = payload.get("sub")
        if user_id is None:
            span.set_attribute("auth.result", "missing_sub")
            raise credentials_exception

        user = db.scalar(select(User).where(User.id == user_id))
        if user is None:
            span.set_attribute("auth.result", "user_not_found")
            raise credentials_exception

        span.set_attribute("user.id", str(user.id))
        return user


def get_active_user(current_user: User = Depends(get_current_user)) -> User:
    """
    일반적인 서비스 API 호출 시 사용되는 의존성입니다.
    현재 로그인한 유저가 탈퇴 유예 기간(DELETED)인 경우 접근을 403으로 차단합니다.
    """
    if current_user.status == UserStatus.DELETED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "ACCOUNT_IN_GRACE_PERIOD", "message": "탈퇴 유예 기간 중인 계정입니다. 서비스 이용을 위해 계정을 복구해주세요."}
        )

    return current_user


def get_optional_user(credentials: HTTPAuthorizationCredentials = Optional[Depends(security)], db: Session = Depends(get_db)) -> Optional[User]:
    """
    비회원(로그인하지 않은 유저)도 접근 가능한 API를 위한 선택적 인증 의존성입니다.
    토큰이 없거나 유효하지 않으면 에러를 띄우지 않고 None을 반환합니다.
    """
    if not credentials:
        return None
    with tracer.start_as_current_span("auth.get_optional_user") as span:
        try:
            payload = jwt.decode(credentials.credentials, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            if payload.get("type") == "refresh":
                return None
            user = db.scalar(select(User).where(User.id == payload.get("sub"), User.status == UserStatus.ACTIVE))
            if user is None:
                return None
            span.set_attribute("user.id", str(user.id))
            return user
        except Exception:
            return None
