from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.user import UserResponse
from app.schemas.register.local import UserRegister
from app.models.models import User, LocalAuth
from app.core.security import get_password_hash
from app.api.deps import validate_local_registration

router = APIRouter()

@router.post("/local", response_model=UserResponse)
def register_local_user(db: Session = Depends(get_db), val_data: dict = Depends(validate_local_registration)):
    """Firebase 토큰으로 본인/중복 확인 후, 이메일/비밀번호 기반 계정을 생성합니다."""
    user_in: UserRegister = val_data["user_in"]
    ci_value = val_data["ci_value"]

    try:
        db_user = db.query(User).filter(User.ci_value == ci_value).first()
        if not db_user:
            db_user = User(username=user_in.username, nickname=user_in.nickname, phone=val_data["formatted_phone"], ci_value=ci_value)
            db.add(db_user)
            db.flush()
        else:
            if db.query(LocalAuth).filter(LocalAuth.user_id == db_user.id).first():
                raise HTTPException(status_code=400, detail={"code": "LOCAL_AUTH_ALREADY_LINKED", "message": "이미 연결된 계정입니다"})
        
        db.add(LocalAuth(user_id=db_user.id, email=user_in.email, password_hash=get_password_hash(user_in.password)))
        db.commit()
        db.refresh(db_user)
        return db_user
    except Exception as e:
        db.rollback()
        if isinstance(e, HTTPException): raise e
        raise HTTPException(status_code=500, detail={"code": "REGISTRATION_FAILED", "message": f"An unexpected error occurred: {str(e)}"})
