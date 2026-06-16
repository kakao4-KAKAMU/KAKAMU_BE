from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.db.session import get_db
from app.models import LocalAuth
from app.schemas.request.auth import LocalLoginRequest
from app.schemas.response.auth import TokenResponse as Token
from app.core.security import verify_password, create_access_token, create_refresh_token
from opentelemetry import trace
from app.schemas.errors import ERROR_LOGIN_FAILED

tracer = trace.get_tracer(__name__)
router = APIRouter()

@router.post(
    "/local",
    response_model=Token,
    responses={401: ERROR_LOGIN_FAILED},
    summary="일반 로그인"
)
def login_local(request: LocalLoginRequest, db: Session = Depends(get_db)) -> dict:
    """JSON 형식(LocalLoginRequest)으로 이메일과 비밀번호를 받아 일반 로그인을 처리합니다."""

    with tracer.start_as_current_span("auth.login.local") as span:
        span.set_attribute("auth.provider", "local")

        if request.email and "@" in request.email: # 이메일은 trace에 안 남기게 설정
            email_domain = request.email.split("@")[-1]
            span.set_attribute("auth.email_domain", email_domain)
    
        # 1. 이메일로 계정 조회
        with tracer.start_as_current_span("auth.login.find_user"):
            stmt = select(LocalAuth).where(LocalAuth.email == request.email)
            local_auth = db.scalar(stmt)

        if not local_auth:
            span.set_attribute("auth.result", "failed")
            span.set_attribute("auth.fail_reason", "user_not_found")
            raise HTTPException(status_code=401, detail={"code": "INVALID_CREDENTIALS", "message": "이메일 또는 비밀번호가 일치하지 않습니다."})

        # 2. 비밀번호 검증
        with tracer.start_as_current_span("auth.login.verify_password"):
            password_valid = verify_password(request.password, local_auth.password_hash)

        if not password_valid:
            span.set_attribute("auth.result", "failed")
            span.set_attribute("auth.fail_reason", "invalid_password")
            raise HTTPException(status_code=401, detail={"code": "INVALID_CREDENTIALS", "message": "이메일 또는 비밀번호가 일치하지 않습니다."})

        # 3. JWT 토큰 발급
        user_id = str(local_auth.user_id)

        # 어떤 방식으로 로그인했는지(provider) 토큰에 포함합니다.
        with tracer.start_as_current_span("auth.login.create_access_token"):
            access_token = create_access_token(data={"sub": user_id, "provider": "local"})

        with tracer.start_as_current_span("auth.login.create_refresh_token"):
            refresh_token = create_refresh_token(data={"sub": user_id, "provider": "local"})

        span.set_attribute("auth.result", "success")
        span.set_attribute("user.id", user_id)

        return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}