from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from uuid import UUID

from app.db.session import get_db
from app.api.deps import get_current_user # Header에서 JWT 검증 및 User 반환
from app.service.notification.notification_service import notification_service
from app.schemas.response.notification import NotificationListResponse

router = APIRouter()

@router.get(
    "/",
    response_model=NotificationListResponse,
    summary="현재 유저의 통합 알림 목록 조회 및 읽음 처리"
)
def get_notifications(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """현재 로그인한 유저의 통합 알림 목록을 불러오고, 진입 즉시 모두 읽음 처리합니다."""
    return notification_service.get_and_read_notifications(db, current_user.id)