from sqlalchemy.orm import Session
from sqlalchemy import select, update, delete
from uuid import UUID
from datetime import datetime, timedelta, timezone
from app.models.notification import Notification, NotificationType
from app.schemas.response.notification import NotificationItem, NotificationListResponse

class NotificationService:
    
    @staticmethod
    def create_notification(
        db: Session,
        receiver_user_id: UUID,
        sender_user_id: UUID,
        type: NotificationType,
        target_type: str,
        target_id: str,
        message: str,
        sender_persona_id: UUID = None,
        sender_nickname: str = None
    ):
        """다른 서비스(좋아요, 댓글 등)에서 이벤트 발생 시 알림을 생성합니다."""
        # 자기 자신의 게시물/댓글에 반응을 남긴 경우 알림 생성 방지
        if receiver_user_id == sender_user_id:
            return
            
        notification = Notification(
            receiver_user_id=receiver_user_id,
            sender_persona_id=sender_persona_id,
            sender_nickname=sender_nickname,
            type=type,
            target_type=target_type,
            target_id=str(target_id),
            message=message
        )
        db.add(notification)
        db.commit()

    @staticmethod
    def get_and_read_notifications(db: Session, receiver_user_id: UUID, limit: int = 50) -> NotificationListResponse:
        """
        읽음 처리 - 알림 탭 진입 시 해당 유저의 통합 알림을 조회하고 
        동시에 안읽은 알림들을 '읽음' 상태로 자동 변경합니다.
        """
        # 1. 안읽은 알림 갯수 카운트
        unread_count_stmt = select(Notification).where(
            Notification.receiver_user_id == receiver_user_id,
            Notification.is_read == False
        )
        unread_count = len(db.scalars(unread_count_stmt).all())

        # 2. 알림 목록 조회 (최신순 정렬)
        stmt = select(Notification).where(
            Notification.receiver_user_id == receiver_user_id
        ).order_by(Notification.created_at.desc()).limit(limit)
        
        notifications = db.scalars(stmt).all()

        # 3. 모두 읽음(is_read=True) 처리
        if unread_count > 0:
            update_stmt = update(Notification).where(
                Notification.receiver_user_id == receiver_user_id,
                Notification.is_read == False
            ).values(is_read=True)
            db.execute(update_stmt)
            db.commit()

        return NotificationListResponse(
            items=notifications,
            unread_count=unread_count # 변경 전(진입 시점) 안읽은 개수 반환
        )

    @staticmethod
    def delete_expired_notifications(db: Session):
        """정책 4: 30일이 지난 알림 영구 삭제 (스케줄러용)"""
        threshold_date = datetime.now(timezone.utc) - timedelta(days=30)
        stmt = delete(Notification).where(Notification.created_at < threshold_date)
        db.execute(stmt)
        db.commit()

notification_service = NotificationService()