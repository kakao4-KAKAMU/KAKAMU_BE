import uuid
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, BigInteger, SmallInteger, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base

class User(Base):
    __tablename__ = "user"
    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)    
    ci_value = Column(String(255), unique=True, nullable=False)    
    phone = Column(String(20), nullable=False)    
    username = Column(String(150), nullable=False)    
    nickname = Column(String(150), nullable=False)    
    status = Column(String(20), default="ACTIVE")
    deleted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())    
    updated_at = Column(DateTime, onupdate=func.now())    

    personas = relationship("Persona", back_populates="user", cascade="all, delete-orphan")    
    posts = relationship("Post", back_populates="user", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="user", cascade="all, delete-orphan")
    following = relationship("Follow", foreign_keys="Follow.follower_id", back_populates="follower", cascade="all, delete-orphan")
    followers = relationship("Follow", foreign_keys="Follow.following_id", back_populates="following_user", cascade="all, delete-orphan")
    local_auths = relationship("LocalAuth", back_populates="user", cascade="all, delete-orphan")    
    social_auths = relationship("SocialAuth", back_populates="user", cascade="all, delete-orphan")    

class LocalAuth(Base):
    __tablename__ = "local_auth"
    auth_id = Column(BigInteger, primary_key=True, autoincrement=True)    
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.id", ondelete="CASCADE"), nullable=False)    
    email = Column(String(100), unique=True, nullable=False)    
    password_hash = Column(String(255), nullable=False)    
    email_verified = Column(SmallInteger, default=0, nullable=False)    

    user = relationship("User", back_populates="local_auths")    

class SocialAuth(Base):
    __tablename__ = "social_auth"
    social_id = Column(BigInteger, primary_key=True)    
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.id", ondelete="CASCADE"), nullable=False)    
    provider = Column(String(20), nullable=False)    
    provider_user_id = Column(String(255), nullable=False)    
    email = Column(String(100), nullable=True) 
    connected_at = Column(DateTime, server_default=func.now())    

    user = relationship("User", back_populates="social_auths")    

    __table_args__ = (
        UniqueConstraint('provider', 'email', name='uq_social_auth_provider_email'),
    )