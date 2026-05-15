from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.login.local import Token
from app.models.models import LocalAuth
from app.core.security import create_access_token, create_refresh_token, verify_password

router = APIRouter()

@router.post("/local", response_model=Token)
def login_local_user(db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    """이메일과 비밀번호로 로그인하여 JWT 토큰을 발급합니다. (Swagger UI 호환)"""
    try:
        # Swagger 연동을 위해 form_data.username을 이메일 입력값으로 사용합니다.
        local_auth = db.query(LocalAuth).filter(LocalAuth.email == form_data.username).first()
        
        if not local_auth or not verify_password(form_data.password, local_auth.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": "LOGIN_FAILED", "message": "Incorrect email or password"},
            )
            
        return {"access_token": create_access_token(data={"sub": str(local_auth.user_id)}), "refresh_token": create_refresh_token(data={"sub": str(local_auth.user_id)}), "token_type": "bearer"}
    except Exception as e:
        if isinstance(e, HTTPException): raise e
        raise HTTPException(status_code=500, detail={"code": "LOGIN_UNEXPECTED_ERROR", "message": f"An unexpected error occurred: {str(e)}"})