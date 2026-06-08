from fastapi import APIRouter, HTTPException
from app.schemas.request.auth import RefreshRequest
from app.schemas.response.auth import TokenResponse as Token
from app.core.security import create_access_token, create_refresh_token
import jwt
from app.core.config import settings

router = APIRouter()

@router.post("/refresh", response_model=Token)
def refresh_access_token(request: RefreshRequest):
    """리프레시 토큰을 검증하고 새로운 액세스 토큰을 발급합니다."""
    try:
        payload = jwt.decode(request.refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail={"code": "INVALID_TOKEN_TYPE", "message": "리프레시 토큰이 아닙니다."})
            
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail={"code": "INVALID_TOKEN_PAYLOAD", "message": "토큰 내 사용자 정보가 없습니다."})
            
        provider = payload.get("provider", "unknown")
        
        new_access_token = create_access_token(data={"sub": user_id, "provider": provider})
        new_refresh_token = create_refresh_token(data={"sub": user_id, "provider": provider})
        return {"access_token": new_access_token, "refresh_token": new_refresh_token, "token_type": "bearer"}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail={"code": "TOKEN_EXPIRED", "message": "리프레시 토큰이 만료되었습니다. 다시 로그인해주세요."})
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail={"code": "INVALID_TOKEN", "message": "유효하지 않은 토큰입니다."})