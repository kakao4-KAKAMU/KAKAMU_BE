from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.schemas.request.auth import SocialLinkRequest, LocalLinkRequest
from app.schemas.response.auth import AccountSettingsResponse
from app.schemas.response.common import SuccessResponse
from app.service.user.auth_link import AuthLinkService
from app.api.deps.auth import get_current_user

router = APIRouter(prefix="/auth-status")

@router.get(
    "", 
    response_model=AccountSettingsResponse,
    summary="현재 계정의 연동 상태 조회"
)
def get_auth_link_status(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> AccountSettingsResponse:
    """현재 유저의 이메일 로그인 및 소셜(카카오, 구글 등) 계정 연동 상태를 조회합니다."""
    return AuthLinkService.get_account_status(db, current_user)

@router.post(
    "/social",
    response_model=SuccessResponse,
    summary="소셜 계정 연동 추가"
)
async def link_social_account(request: SocialLinkRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> dict:
    """새로운 소셜 계정(카카오 등)을 현재 로그인된 계정에 연결(Link)합니다."""
    await AuthLinkService.link_social_account(db, current_user.id, request)
    return {"status": "success", "message": f"{request.provider} 계정이 성공적으로 연동되었습니다."}

@router.post(
    "/local",
    response_model=SuccessResponse,
    summary="로컬(이메일/비밀번호) 계정 연동 추가"
)
def link_local_account(request: LocalLinkRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> dict:
    """현재 로그인된 소셜 계정에 이메일/비밀번호 기반의 로그인 수단을 추가로 연동합니다."""
    AuthLinkService.link_local_account(db, current_user.id, request)
    return {"status": "success", "message": "이메일 로그인 연동이 완료되었습니다."}

@router.delete(
    "/social/{provider}",
    response_model=SuccessResponse,
    summary="소셜 계정 연동 해제"
)
def unlink_social_account(provider: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> dict:
    """연동된 소셜 계정(카카오 등)의 연결을 해제(Unlink)합니다. (단, 유일한 로그인 수단인 경우 실패)"""
    AuthLinkService.unlink_social_account(db, current_user.id, provider)
    return {"status": "success", "message": f"{provider} 계정 연동이 해제되었습니다."}