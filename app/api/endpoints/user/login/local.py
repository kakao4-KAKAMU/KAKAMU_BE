from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models import LocalAuth, Persona
from app.schemas.login.local import LocalLoginRequest, Token
from app.core.security import verify_password, create_access_token, create_refresh_token

router = APIRouter()

@router.post("/local", response_model=Token)
def login_local(request: LocalLoginRequest, db: Session = Depends(get_db)):
    """JSON 형식(LocalLoginRequest)으로 이메일과 비밀번호를 받아 일반 로그인을 처리합니다."""
    
    # 1. 이메일로 계정 조회
    local_auth = db.query(LocalAuth).filter(LocalAuth.email == request.email).first()
    if not local_auth:
        raise HTTPException(status_code=401, detail={"code": "INVALID_CREDENTIALS", "message": "이메일 또는 비밀번호가 일치하지 않습니다."})
        
    # 2. 비밀번호 검증
    if not verify_password(request.password, local_auth.password_hash):
        raise HTTPException(status_code=401, detail={"code": "INVALID_CREDENTIALS", "message": "이메일 또는 비밀번호가 일치하지 않습니다."})
        
    # 3. 유저의 메인 페르소나 조회
    main_persona = db.query(Persona).filter(
        Persona.user_id == local_auth.user_id,
        Persona.is_main == 1,
        Persona.status == "ACTIVE"
    ).first()
    persona_id_str = str(main_persona.id) if main_persona else None

    # 4. JWT 토큰 발급 (persona_id 포함)
    user_id = str(local_auth.user_id)
    # 어떤 방식으로 로그인했는지(provider) 토큰에 포함합니다.
    access_token = create_access_token(data={"sub": user_id, "provider": "local", "persona_id": persona_id_str})
    refresh_token = create_refresh_token(data={"sub": user_id, "provider": "local", "persona_id": persona_id_str})
    
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}