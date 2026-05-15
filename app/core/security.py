from datetime import datetime, timedelta, timezone
import hashlib
import bcrypt
import jwt
from app.core.config import settings

def get_password_hash(password: str) -> str:
    # 1단계: 긴 비밀번호를 SHA-256으로 해시 (64바이트 고정)
    password_hash = hashlib.sha256(password.encode()).hexdigest().encode()
    # 2단계: bcrypt로 다시 해싱
    hashed = bcrypt.hashpw(password_hash, bcrypt.gensalt())
    return hashed.decode()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    # 1단계: SHA-256으로 변환
    password_hash = hashlib.sha256(plain_password.encode()).hexdigest().encode()
    # 2단계: bcrypt 검증
    return bcrypt.checkpw(password_hash, hashed_password.encode())

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "refresh"}) # 액세스 토큰과 구분하기 위한 식별자
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt