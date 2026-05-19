import enum
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base

class BlockLevel(str, enum.Enum):
    PERSONA = "PERSONA"
    USER = "USER"

class Follow(Base):
    __tablename__ = "follow"
    follower_id = Column(Integer, ForeignKey("persona.id", ondelete="CASCADE"), primary_key=True)    
    following_id = Column(Integer, ForeignKey("persona.id", ondelete="CASCADE"), primary_key=True)    
    created_at = Column(DateTime, server_default=func.now())    

    follower = relationship("Persona", foreign_keys=[follower_id], back_populates="following")    
    following_persona = relationship("Persona", foreign_keys=[following_id], back_populates="followers")    

class Block(Base):
    __tablename__ = "block"
    blocker_id = Column(Integer, ForeignKey("persona.id", ondelete="CASCADE"), primary_key=True, index=True)
    blocked_id = Column(Integer, ForeignKey("persona.id", ondelete="CASCADE"), primary_key=True, index=True)
    level = Column(String(20), default=BlockLevel.PERSONA.value)
    created_at = Column(DateTime, server_default=func.now())