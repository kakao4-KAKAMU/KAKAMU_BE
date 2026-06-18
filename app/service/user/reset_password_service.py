from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models import User, LocalAuth, SocialAuth
from app.core.security import get_password_hash, verify_password
from app.schemas.request.auth import PasswordResetRequest
from app.core.firebase import verify_firebase_token

class ResetPasswordService:
    
    @staticmethod
    def reset_password(db: Session, request: PasswordResetRequest) -> None:
        # 1. Firebase 토큰 검증 및 전화번호 추출
        phone_number = verify_firebase_token(request.firebase_id_token)
        if not phone_number:
            raise HTTPException(
                status_code=400, 
                detail={"code": "INVALID_FIREBASE_TOKEN", "message": "유효하지 않거나 만료된 Firebase 토큰입니다."}
            )
            
        formatted_phone = phone_number.replace("+82", "0") if phone_number.startswith("+82") else phone_number

        # 2. 전화번호로 가입된 계정이 있는지 우선 확인
        user = db.scalar(select(User).where(User.phone == formatted_phone))
        if not user:
            raise HTTPException(
                status_code=404, 
                detail={"code": "USER_NOT_FOUND", "message": "인증된 전화번호로 가입된 계정을 찾을 수 없습니다."}
            )

        # 3. 해당 이메일의 LocalAuth 연동 여부 확인 (소셜 유저 차단 방어 로직)
        local_auth = db.scalar(select(LocalAuth).where(LocalAuth.user_id == user.id, LocalAuth.email == request.email))
        if not local_auth:
            # 전화번호로 가입된 기록은 있으나 LocalAuth가 없는 경우 (소셜 전용 계정이거나 이메일 오입력)
            is_social_only = db.scalar(select(SocialAuth).where(SocialAuth.user_id == user.id)) is not None
            if is_social_only:
                raise HTTPException(status_code=400, detail={"code": "SOCIAL_USER", "message": "소셜 로그인으로 가입된 계정입니다. 해당 소셜 서비스를 통해 로그인해주세요."})
                
            raise HTTPException(
                status_code=404, 
                detail={"code": "USER_NOT_FOUND", "message": "입력하신 이메일과 인증된 전화번호가 일치하는 계정을 찾을 수 없습니다."}
            )

        # 4. 새 비밀번호가 기존 비밀번호와 동일한지 검사
        if verify_password(request.new_password, local_auth.password_hash):
            raise HTTPException(
                status_code=400,
                detail={"code": "SAME_PASSWORD", "message": "새 비밀번호는 기존 비밀번호와 다르게 설정해야 합니다."}
            )

        # 5. 비밀번호 업데이트 (해싱 처리)
        local_auth.password_hash = get_password_hash(request.new_password)
        
        try:
            db.commit()
        except Exception:
            db.rollback()
            raise HTTPException(status_code=500, detail={"code": "DB_COMMIT_ERROR", "message": "비밀번호 갱신 중 서버 오류가 발생했습니다."})

reset_password_service = ResetPasswordService()