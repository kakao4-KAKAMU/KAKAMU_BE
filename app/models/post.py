import enum
from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime, JSON, SmallInteger, Index, Enum, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base


class PostStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class Post(Base):
    __tablename__ = "post"
    id = Column(Integer, primary_key=True)    
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.id", ondelete="CASCADE"), nullable=False)    
    persona_id = Column(UUID(as_uuid=True), ForeignKey("persona.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(255), nullable=False)    
    content = Column(Text)    
    image_urls = Column(JSON) 
    is_spoiler = Column(SmallInteger, default=0) 
    status = Column(Enum(PostStatus), default=PostStatus.ACTIVE, nullable=False)
    is_analyzed = Column(SmallInteger, default=0)    
    created_at = Column(DateTime, server_default=func.now())    
    updated_at = Column(DateTime, onupdate=func.now())    

    # [성능 최적화] 서브쿼리 대신 물리적 컬럼으로 관리 (Redis Sync Task가 5분 주기로 업데이트)
    like_count = Column(Integer, default=0, nullable=False)

    user = relationship("User", back_populates="posts")    
    persona = relationship("Persona")
    comments = relationship("Comment", back_populates="post", cascade="all, delete-orphan")    
    movies = relationship("Movie", secondary="post_movie", back_populates="posts")    
    hashtags = relationship("Hashtag", secondary="post_hashtag", back_populates="posts")    
    mentions = relationship("User", secondary="post_mention", backref="mentioned_in_posts")    

    __table_args__ = (
        # 메인 피드: ACTIVE 게시물 최신순 (id DESC keyset pagination)
        Index(
            'ix_post_status_id_desc',
            'status',
            id.desc(),
            postgresql_where=text("status = 'ACTIVE'"),
        ),
        # 프로필 게시물·게시물 수: user_id별 ACTIVE 최신순
        Index(
            'ix_post_user_active_id_desc',
            'user_id',
            id.desc(),
            postgresql_where=text("status = 'ACTIVE'"),
        ),
        # 워커/배치: user_id 기준 전체 상태 조회
        Index('ix_post_user_id', 'user_id'),
        # 검색: title/content 부분 일치 (pg_trgm, ACTIVE만)
        Index(
            'ix_post_title_content_trgm',
            'title',
            'content',
            postgresql_using='gin',
            postgresql_ops={'title': 'gin_trgm_ops', 'content': 'gin_trgm_ops'},
            postgresql_where=text("status = 'ACTIVE'"),
        ),
        # for-you fallback·인기순 검색: like_count DESC, id DESC
        Index(
            'ix_post_active_like_count_id_desc',
            like_count.desc(),
            id.desc(),
            postgresql_where=text("status = 'ACTIVE'"),
        ),
    )

class PostMovie(Base):
    __tablename__ = "post_movie"
    post_id = Column(Integer, ForeignKey("post.id", ondelete="CASCADE"), primary_key=True)    
    movie_id = Column(UUID(as_uuid=True), ForeignKey("movie.id", ondelete="CASCADE"), primary_key=True)    

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


class PostHashtagAgg(Base):
    __tablename__ = "post_hashtag_agg"

    post_id = Column(Integer, ForeignKey("post.id"), primary_key=True)
    hashtags = Column(JSONB, nullable=False)


class PostMentionAgg(Base):
    __tablename__ = "post_mention_agg"

    post_id = Column(Integer, ForeignKey("post.id"), primary_key=True)
    mentions = Column(JSONB, nullable=False)


class PostMovieAgg(Base):
    __tablename__ = "post_movie_agg"

    post_id = Column(Integer, ForeignKey("post.id"), primary_key=True)
    movies = Column(JSONB, nullable=False)


class PostCommentCount(Base):
    __tablename__ = "post_comment_count"

    post_id = Column(Integer, ForeignKey("post.id"), primary_key=True)
    comment_count = Column(Integer, nullable=False)