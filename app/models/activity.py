from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, SmallInteger, Numeric, Double, Text, JSON, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base

class Comment(Base):
    __tablename__ = "comment"
    id = Column(Integer, primary_key=True)    
    post_id = Column(Integer, ForeignKey("post.id", ondelete="CASCADE"), nullable=False)    
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.id", ondelete="CASCADE"), nullable=False)    
    persona_id = Column(UUID(as_uuid=True), ForeignKey("persona.id", ondelete="SET NULL"), nullable=True)
    parent_id = Column(Integer, ForeignKey("comment.id", ondelete="CASCADE"), nullable=True) 
    content = Column(String(1000))    
    is_spoiler = Column(SmallInteger, default=0) 
    status = Column(String(20), default="ACTIVE") 
    created_at = Column(DateTime, server_default=func.now())    
    updated_at = Column(DateTime, onupdate=func.now())    
    is_pinned = Column(SmallInteger, default=0)    
    is_analyzed = Column(SmallInteger, default=0)    

    post = relationship("Post", back_populates="comments")    
    user = relationship("User", back_populates="comments")    
    replies = relationship("Comment", back_populates="parent", cascade="all, delete-orphan")    
    parent = relationship("Comment", back_populates="replies", remote_side=[id])    
    mentions = relationship("User", secondary="comment_mention", backref="mentioned_in_comments")    

class CommentMention(Base):
    __tablename__ = "comment_mention"
    comment_id = Column(Integer, ForeignKey("comment.id", ondelete="CASCADE"), primary_key=True)    
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.id", ondelete="CASCADE"), primary_key=True)    

class LikeLog(Base):
    __tablename__ = "like_log"
    id = Column(Integer, primary_key=True, autoincrement=True)    
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.id", ondelete="CASCADE"), nullable=False)    
    persona_id = Column(UUID(as_uuid=True), ForeignKey("persona.id", ondelete="SET NULL"), nullable=True) # ML 점수 롤백을 위해 액션을 발생시킨 주체 기록
    target_type = Column(String(20), nullable=False) 
    target_id = Column(Integer, nullable=False)    
    is_active = Column(SmallInteger, default=1) 
    created_at = Column(DateTime, server_default=func.now())    
    updated_at = Column(DateTime, onupdate=func.now())    

    __table_args__ = (
        UniqueConstraint('user_id', 'target_type', 'target_id', name='uq_likelog_user_target'),
        Index('ix_likelog_target', 'target_type', 'target_id'),
    )

class SemanticAnalysis(Base):
    __tablename__ = "semantic_analysis"
    id = Column(Integer, primary_key=True)    
    target_type = Column(String(30))    
    target_id = Column(Integer)    
    summary = Column(Text)    
    keywords = Column(JSON) 

    __table_args__ = (
        Index('ix_semantic_target', 'target_type', 'target_id'),
    )