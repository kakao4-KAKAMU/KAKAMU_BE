from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime, JSON, SmallInteger, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base

class Post(Base):
    __tablename__ = "post"
    id = Column(Integer, primary_key=True)    
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.id", ondelete="CASCADE"), nullable=False)    
    persona_id = Column(UUID(as_uuid=True), ForeignKey("persona.id", ondelete="SET NULL"), nullable=True) # 화면 렌더링을 위한 작성 당시 페르소나
    title = Column(String(255), nullable=False)    
    content = Column(Text)    
    image_urls = Column(JSON) 
    is_spoiler = Column(SmallInteger, default=0) 
    status = Column(String(20), default="ACTIVE") 
    is_analyzed = Column(SmallInteger, default=0)    
    created_at = Column(DateTime, server_default=func.now())    
    updated_at = Column(DateTime, onupdate=func.now())    

    # [성능 최적화] 서브쿼리 대신 물리적 컬럼으로 관리 (Redis Sync Task가 5분 주기로 업데이트)
    like_count = Column(Integer, default=0, nullable=False, index=True)

    user = relationship("User", back_populates="posts")    
    persona = relationship("Persona") # 게시물 작성 페르소나 정보 조회용
    comments = relationship("Comment", back_populates="post", cascade="all, delete-orphan")    
    movies = relationship("Movie", secondary="post_movie", back_populates="posts")    
    hashtags = relationship("Hashtag", secondary="post_hashtag", back_populates="posts")    
    mentions = relationship("User", secondary="post_mention", backref="mentioned_in_posts")    

    __table_args__ = (
        Index('ix_post_title_trgm', 'title', postgresql_using='gin', postgresql_ops={'title': 'gin_trgm_ops'}),
        Index('ix_post_content_trgm', 'content', postgresql_using='gin', postgresql_ops={'content': 'gin_trgm_ops'}),
    )

class PostMovie(Base):
    __tablename__ = "post_movie"
    post_id = Column(Integer, ForeignKey("post.id", ondelete="CASCADE"), primary_key=True)    
    movie_id = Column(Integer, ForeignKey("movie.id", ondelete="CASCADE"), primary_key=True)    

class Hashtag(Base):
    __tablename__ = "hashtag"
    id = Column(Integer, primary_key=True, autoincrement=True)    
    normalized_keyword = Column(String(100), unique=True, nullable=False)    

    posts = relationship("Post", secondary="post_hashtag", back_populates="hashtags")    

class PostHashtag(Base):
    __tablename__ = "post_hashtag"
    post_id = Column(Integer, ForeignKey("post.id", ondelete="CASCADE"), primary_key=True)    
    hashtag_id = Column(Integer, ForeignKey("hashtag.id", ondelete="CASCADE"), primary_key=True)    

class PostMention(Base):
    __tablename__ = "post_mention"
    post_id = Column(Integer, ForeignKey("post.id", ondelete="CASCADE"), primary_key=True)    
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.id", ondelete="CASCADE"), primary_key=True)