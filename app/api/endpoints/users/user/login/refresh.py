from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.schemas.request.auth import RefreshRequest
from app.schemas.response.auth import TokenResponse as Token
from app.core.security import create_access_token, create_refresh_token
from app.db.session import get_db
from app.models import User
import jwt
from app.core.config import settings
from app.schemas.errors import ERROR_REFRESH_TOKEN_FAILURES

router = APIRouter()

@router.post(
    "/refresh",
    response_model=Token,
    responses={401: ERROR_REFRESH_TOKEN_FAILURES},
    summary="액세스 토큰 갱신"
)
def refresh_access_token(request: RefreshRequest, db: Session = Depends(get_db)) -> dict:
    """리프레시 토큰을 검증하고 새로운 액세스 토큰을 발급합니다."""
    try:
        payload = jwt.decode(request.refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail={"code": "INVALID_TOKEN_TYPE", "message": "리프레시 토큰이 아닙니다."})
            
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail={"code": "INVALID_TOKEN_PAYLOAD", "message": "토큰 내 사용자 정보가 없습니다."})
            
        # DB에서 유저 존재 여부 및 활성(탈퇴) 상태 확인
        user = db.scalar(select(User).where(User.id == user_id))
        if not user or user.status == "DELETED":
            raise HTTPException(status_code=401, detail={"code": "USER_NOT_ACTIVE", "message": "유효하지 않거나 탈퇴 처리된 계정입니다. 다시 로그인해주세요."})
            
        provider = payload.get("provider", "unknown")
        
        new_access_token = create_access_token(data={"sub": user_id, "provider": provider})
        new_refresh_token = create_refresh_token(data={"sub": user_id, "provider": provider})
        return {"access_token": new_access_token, "refresh_token": new_refresh_token, "token_type": "bearer"}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail={"code": "TOKEN_EXPIRED", "message": "리프레시 토큰이 만료되었습니다. 다시 로그인해주세요."})
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail={"code": "INVALID_TOKEN", "message": "유효하지 않은 토큰입니다."})