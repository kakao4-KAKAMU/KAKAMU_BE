import hashlib
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.user import UserLogin, Token
from app.models.models import LocalAuth
from app.core.security import create_access_token, verify_password

router = APIRouter()

@router.post("/login", response_model=Token)
def login_user(user_in: UserLogin, db: Session = Depends(get_db)):
    """이메일과 비밀번호로 로그인하여 JWT 토큰을 발급합니다."""
    try:
        local_auth = db.query(LocalAuth).filter(LocalAuth.email == user_in.email).first()
        
        # SHA-256 + BCrypt 검증: 입력된 비밀번호를 SHA-256으로 해싱한 후, 저장된 BCrypt 해시와 비교
        sha256_password = hashlib.sha256(user_in.password.encode('utf-8')).hexdigest()
        if not local_auth or not verify_password(sha256_password, local_auth.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": "LOGIN_FAILED", "message": "Incorrect email or password"},
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        # JWT 토큰 생성 (user_id를 payload에 포함)
        access_token = create_access_token(data={"sub": str(local_auth.user_id)})
        return {"access_token": access_token, "token_type": "bearer"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Login Error: {str(e)}")
        raise HTTPException(status_code=500, detail={"code": "LOGIN_UNEXPECTED_ERROR", "message": f"An unexpected error occurred: {str(e)}"})