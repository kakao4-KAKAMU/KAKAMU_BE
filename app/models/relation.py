import enum
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base

class BlockLevel(str, enum.Enum):
    PERSONA = "PERSONA"
    USER = "USER"

class Follow(Base):
    __tablename__ = "follow"
    follower_id = Column(UUID(as_uuid=True), ForeignKey("user.id", ondelete="CASCADE"), primary_key=True)    
    following_id = Column(UUID(as_uuid=True), ForeignKey("user.id", ondelete="CASCADE"), primary_key=True)    
    created_at = Column(DateTime, server_default=func.now())    

    follower = relationship("User", foreign_keys=[follower_id], back_populates="following")    
    following_user = relationship("User", foreign_keys=[following_id], back_populates="followers")    

class Block(Base):
    __tablename__ = "block"
    blocker_id = Column(UUID(as_uuid=True), ForeignKey("user.id", ondelete="CASCADE"), primary_key=True, index=True)
    blocked_id = Column(UUID(as_uuid=True), ForeignKey("user.id", ondelete="CASCADE"), primary_key=True, index=True)
    level = Column(String(20), default=BlockLevel.USER.value)
    created_at = Column(DateTime, server_default=func.now())