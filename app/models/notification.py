import enum
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base

class NotificationType(str, enum.Enum):
    FOLLOW = "FOLLOW"
    LIKE = "LIKE"
    COMMENT = "COMMENT"
    MENTION = "MENTION"

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    # 유저 단위 알림 통합 (모든 페르소나의 알림을 유저가 모아봄)
    receiver_user_id = Column(UUID(as_uuid=True), index=True, nullable=False)
    
    sender_persona_id = Column(UUID(as_uuid=True), nullable=True)
    sender_nickname = Column(String, nullable=True)
    
    type = Column(Enum(NotificationType), nullable=False)
    target_type = Column(String, nullable=False) # 예: "POST", "COMMENT", "USER"
    target_id = Column(String, nullable=False)   # 딥링크 이동을 위한 타겟 ID
    message = Column(String, nullable=False)     # 알림 메시지 포맷팅 결과
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)