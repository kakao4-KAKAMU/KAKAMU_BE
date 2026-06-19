from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.db.session import get_db
from app.schemas.mapper.user import UserMapper
from app.schemas.response.user import UserResponse
from app.schemas.request.auth import UserRegister, LocalLinkRequest
from app.models import User, LocalAuth, SocialAuth
from app.core.security import get_password_hash
from app.api.deps import validate_local_registration, get_current_user
from app.schemas.errors import (
    ERROR_LOCAL_AUTH_ALREADY_LINKED,
    ERROR_REGISTRATION_FAILED,
    ERROR_LOCAL_LINK_FAILURES
)

router = APIRouter()

@router.post(
    "/local",
    response_model=UserResponse,
    responses={400: ERROR_LOCAL_AUTH_ALREADY_LINKED, 500: ERROR_REGISTRATION_FAILED},
    summary="일반 회원가입"
)
def register_local_user(db: Session = Depends(get_db), val_data: dict = Depends(validate_local_registration)) -> UserResponse:
    """Firebase 토큰으로 본인/중복 확인 후, 이메일/비밀번호 기반 계정을 생성합니다."""
    user_in: UserRegister = val_data["user_in"]
    ci_value = val_data["ci_value"]

    try:
        db_user = db.scalar(select(User).where(User.ci_value == ci_value))
        if not db_user:
            db_user = User(username=user_in.username, nickname=user_in.nickname, phone=val_data["formatted_phone"], ci_value=ci_value)
            db.add(db_user)
            db.flush()
        else:
            if db.scalar(select(LocalAuth).where(LocalAuth.user_id == db_user.id)):
                raise HTTPException(status_code=400, detail={"code": "LOCAL_AUTH_ALREADY_LINKED", "message": "이미 연결된 계정입니다"})
        
        db.add(LocalAuth(user_id=db_user.id, email=user_in.email, password_hash=get_password_hash(user_in.password)))
        db.commit()
        db.refresh(db_user)
        return UserMapper.to_account(db_user)
    except Exception as e:
        db.rollback()
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail={"code": "REGISTRATION_FAILED", "message": f"An unexpected error occurred: {str(e)}"})

@router.post(
    "/local/link",
    response_model=UserResponse,
    responses={400: ERROR_LOCAL_LINK_FAILURES},
    summary="로컬(이메일) 계정 추가 연동"
)
def link_local_user(
    request: LocalLinkRequest,
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
) -> UserResponse:
    """로그인된 상태에서 이메일(로컬) 계정을 추가 연동합니다. (본인인증 생략)"""
    
    # 1. 사용할 이메일 결정 (입력값이 없으면 기존 소셜 계정에서 끌어오기)
    link_email = request.email
    if not link_email:
        social_auth = db.scalar(select(SocialAuth).where(SocialAuth.user_id == current_user.id))
        if social_auth and social_auth.email:
            link_email = social_auth.email
        else:
            raise HTTPException(status_code=400, detail={"code": "EMAIL_REQUIRED", "message": "소셜 계정에 등록된 이메일이 없습니다. 연동할 이메일을 직접 입력해주세요."})
            
    # 2. 이미 로컬 계정이 연동되어 있는지 확인
    if db.scalar(select(LocalAuth).where(LocalAuth.user_id == current_user.id)):
        raise HTTPException(status_code=400, detail={"code": "LOCAL_AUTH_ALREADY_LINKED", "message": "이미 이메일 로그인 정보가 연동되어 있습니다."})
        
    # 3. 다른 사용자가 이미 이 이메일을 사용 중인지 확인
    if db.scalar(select(LocalAuth).where(LocalAuth.email == link_email)):
        raise HTTPException(status_code=400, detail={"code": "DUPLICATE_EMAIL", "message": "이미 등록된 이메일입니다."})
        
    db.add(LocalAuth(user_id=current_user.id, email=link_email, password_hash=get_password_hash(request.password)))
    db.commit()
    db.refresh(current_user)
    return UserMapper.to_account(current_user)
