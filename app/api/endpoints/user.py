import hashlib
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.user import UserRegister, UserResponse
from app.schemas.social_auth import SocialRegisterRequest, TokenResponse
from app.models.models import User, LocalAuth, SocialAuth
from app.core.security import get_password_hash, create_access_token
from app.api.deps import get_current_user
from app.core.firebase import verify_firebase_token

# APIRouter 인스턴스 생성
router = APIRouter()

@router.get("/me", response_model=UserResponse)
def get_user_me(current_user: User = Depends(get_current_user)):
    """현재 로그인된 사용자의 정보를 반환합니다."""
    return current_user

@router.post("/register/local", response_model=UserResponse)
def register_user(user_in: UserRegister, db: Session = Depends(get_db)):
    """Firebase 토큰으로 본인/중복 확인 후, 이메일/비밀번호 기반 계정을 생성합니다."""
    try:
        # Firebase 토큰 검증
        phone_number = verify_firebase_token(user_in.firebase_id_token)
        if not phone_number:
            raise HTTPException(status_code=400, detail={"code": "INVALID_FIREBASE_TOKEN", "message": "Invalid or expired Firebase token"})
            
        # +8210... 형태의 번호를 010... 으로 변환
        formatted_phone = phone_number.replace("+82", "0") if phone_number.startswith("+82") else phone_number
       
        # CI 값 생성: SHA-256(이름 + 전화번호)
        ci_string = f"{user_in.username}{formatted_phone}"
        ci_value = hashlib.sha256(ci_string.encode('utf-8')).hexdigest()
        
        # 이메일 중복 체크 (LocalAuth 전용)
        if db.query(LocalAuth).filter(LocalAuth.email == user_in.email).first():
            raise HTTPException(status_code=400, detail={"code": "DUPLICATE_EMAIL", "message": "Email already registered"})
        
        # 기존 유저 조회 (CI 기반 통합)
        db_user = db.query(User).filter(User.ci_value == ci_value).first()
        
        if not db_user:
            # 1. User 생성
            db_user = User(
                username=user_in.username,
                nickname=user_in.nickname,
                phone=formatted_phone,
                ci_value=ci_value
            )
            db.add(db_user)
            db.flush()
        else:
            # 동일 CI 유저 존재 시 LocalAuth 연결 상태 확인
            if db.query(LocalAuth).filter(LocalAuth.user_id == db_user.id).first():
                raise HTTPException(status_code=400, detail={"code": "LOCAL_AUTH_ALREADY_LINKED", "message": "이미 연결된 계정입니다"})
        
        # 2. LocalAuth 생성 (비밀번호: SHA-256 적용 후 BCrypt 암호화)
        sha256_password = hashlib.sha256(user_in.password.encode('utf-8')).hexdigest()
        db_local_auth = LocalAuth(
            user_id=db_user.id,
            email=user_in.email,
            password_hash=get_password_hash(sha256_password)
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
        raise HTTPException(status_code=500, detail={"code": "REGISTRATION_FAILED", "message": f"An unexpected error occurred: {str(e)}"})

@router.post("/register/social", response_model=TokenResponse)
def social_register(request: SocialRegisterRequest, db: Session = Depends(get_db)):
    """추가 정보를 받아 User와 SocialAuth를 생성하고 JWT를 발급합니다."""
    try:
        # CI 값 생성: SHA-256(이름 + 전화번호)
        ci_string = f"{request.username}{request.phone}"
        ci_value = hashlib.sha256(ci_string.encode('utf-8')).hexdigest()
        
        # 1. 이메일 중복 체크 (SocialAuth 테이블 내 해당 제공자 기준)
        if request.email and db.query(SocialAuth).filter(
            SocialAuth.provider == request.provider,
            SocialAuth.email == request.email
        ).first():
            raise HTTPException(status_code=400, detail={"code": "DUPLICATE_EMAIL", "message": "이미 등록된 이메일입니다."})
            
        # 2. 기존 유저 조회 (CI 기반 통합)
        db_user = db.query(User).filter(User.ci_value == ci_value).first()

        if not db_user:
            # User 테이블 생성
            db_user = User(
                username=request.username,
                nickname=request.nickname,
                phone=request.phone,
                ci_value=ci_value
            )
            db.add(db_user)
            db.flush() # db_user의 id를 얻기 위해 flush
        else:
            # 중복 차단: 이미 동일한 Provider가 연결된 상태라면 진행 차단
            existing_social = db.query(SocialAuth).filter(
                SocialAuth.user_id == db_user.id,
                SocialAuth.provider == request.provider
            ).first()
            if existing_social:
                raise HTTPException(status_code=400, detail={"code": "SOCIAL_AUTH_ALREADY_LINKED", "message": "이미 연결된 계정입니다"})
        
        # 3. SocialAuth 테이블 연동 정보 생성
        new_social = SocialAuth(
            user_id=db_user.id,
            provider=request.provider,
            provider_user_id=request.provider_user_id,
            email=request.email
        )
        db.add(new_social)
        
        db.commit()
        
        # 4. JWT 토큰 발급
        access_token = create_access_token(data={"sub": str(db_user.id)})
        return TokenResponse(access_token=access_token, is_new_user=False)
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"Social Register Error: {str(e)}")
        raise HTTPException(status_code=500, detail={"code": "REGISTRATION_FAILED", "message": f"An unexpected error occurred: {str(e)}"})

@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    """특정 사용자 정보를 조회합니다."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail={"code": "USER_NOT_FOUND", "message": "User not found"})
    return user
