from app.models.notification import Notification as NotificationModel
from app.schemas.base.notification import Notification


class NotificationMapper:
    @staticmethod
    def to_notification(notification: NotificationModel) -> Notification:
        return Notification(
            id=notification.id,
            receiver_user_id=notification.receiver_user_id,
            sender_persona_id=notification.sender_persona_id,
            sender_nickname=notification.sender_nickname,
            type=notification.type.value if hasattr(notification.type, "value") else notification.type,
            target_type=notification.target_type,
            target_id=notification.target_id,
            message=notification.message,
            is_read=notification.is_read,
            created_at=notification.created_at,
        )
