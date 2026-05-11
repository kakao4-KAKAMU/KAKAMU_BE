from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.user import UserRegister, UserLogin, UserResponse, Token
from app.models.models import User, LocalAuth
from app.core.security import create_access_token, get_password_hash, verify_password
from app.api.deps import get_current_user
from app.core.firebase import verify_firebase_token

# APIRouter 인스턴스 생성
router = APIRouter()

@router.get("/me", response_model=UserResponse)
def get_user_me(current_user: User = Depends(get_current_user)):
    """현재 로그인된 사용자의 정보를 반환합니다."""
    return current_user

@router.post("/register", response_model=UserResponse)
def register_user(user_in: UserRegister, db: Session = Depends(get_db)):
    """Firebase 토큰으로 본인/중복 확인 후, 이메일/비밀번호 기반 계정을 생성합니다."""
    try:
        # Firebase 토큰 검증
        phone_number = verify_firebase_token(user_in.firebase_id_token)
        if not phone_number:
            raise HTTPException(status_code=400, detail="Invalid or expired Firebase token")
            
        # +8210... 형태의 번호를 010... 으로 변환
        formatted_phone = phone_number.replace("+82", "0") if phone_number.startswith("+82") else phone_number

        # 전화번호 중복 체크 추가
        if db.query(User).filter(User.phone == formatted_phone).first():
            raise HTTPException(status_code=400, detail="Phone number already registered")

        # ci_value 중복 체크
        if db.query(User).filter(User.ci_value == user_in.ci_value).first():
            raise HTTPException(status_code=400, detail="User with this CI value already exists")
            
        # 이메일 중복 체크 (LocalAuth)
        if db.query(LocalAuth).filter(LocalAuth.email == user_in.email).first():
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # 1. User 생성
        db_user = User(
            username=user_in.username,
            nickname=user_in.nickname,
            phone=formatted_phone,
            ci_value=user_in.ci_value
        )
        db.add(db_user)
        db.flush()
        
        # 2. LocalAuth 생성
        db_local_auth = LocalAuth(
            user_id=db_user.id,
            email=user_in.email,
            password_hash=get_password_hash(user_in.password)
        )
        db.add(db_local_auth)
        
        db.commit()
        db.refresh(db_user)
        
        return db_user
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"Register Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

@router.post("/login", response_model=Token)
def login_user(user_in: UserLogin, db: Session = Depends(get_db)):
    """이메일과 비밀번호로 로그인하여 JWT 토큰을 발급합니다."""
    try:
        local_auth = db.query(LocalAuth).filter(LocalAuth.email == user_in.email).first()
        
        if not local_auth or not verify_password(user_in.password, local_auth.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        # JWT 토큰 생성 (user_id를 payload에 포함)
        access_token = create_access_token(data={"sub": str(local_auth.user_id)})
        return {"access_token": access_token, "token_type": "bearer"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Login Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")

@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    """특정 사용자 정보를 조회합니다."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
