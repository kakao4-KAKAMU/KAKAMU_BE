from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime, Numeric, SmallInteger, BigInteger, JSON, Double, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base # 프로젝트의 Base 클래스 경로에 맞춰 수정

# --- 1. 인증 및 사용자 관련 테이블 ---

class User(Base):
    __tablename__ = "user"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)    
    ci_value = Column(String(255), unique=True, nullable=False)    
    phone = Column(String(20), nullable=False)    
    username = Column(String(150), nullable=False)    
    nickname = Column(String(150), nullable=False)    
    created_at = Column(DateTime, server_default=func.now())    
    updated_at = Column(DateTime, onupdate=func.now())    

    personas = relationship("Persona", back_populates="user", cascade="all, delete-orphan")    
    local_auths = relationship("LocalAuth", back_populates="user", cascade="all, delete-orphan")    
    social_auths = relationship("SocialAuth", back_populates="user", cascade="all, delete-orphan")    

class LocalAuth(Base):
    __tablename__ = "local_auth"
    auth_id = Column(BigInteger, primary_key=True, autoincrement=True)    
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False)    
    email = Column(String(100), unique=True, nullable=False)    
    password_hash = Column(String(255), nullable=False)    
    email_verified = Column(SmallInteger, default=0, nullable=False)    

    user = relationship("User", back_populates="local_auths")    

class SocialAuth(Base):
    __tablename__ = "social_auth"
    social_id = Column(BigInteger, primary_key=True)    
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False)    
    provider = Column(String(20), nullable=False)    
    provider_user_id = Column(String(255), nullable=False)    
    email = Column(String(100), nullable=True) # 소셜 플랫폼에서 받은 이메일
    connected_at = Column(DateTime, server_default=func.now())    

    user = relationship("User", back_populates="social_auths")    

    __table_args__ = (
        UniqueConstraint('provider', 'email', name='uq_social_auth_provider_email'),
    )

# --- 2. 페르소나(프로필) 및 소셜 기능 테이블 ---

class Persona(Base):
    __tablename__ = "persona"
    id = Column(Integer, primary_key=True, autoincrement=True)    
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False)    
    nickname = Column(String(50), nullable=False) # 2~12자 정책 적용
    tag = Column(String(10), nullable=False) # 3~5자리 숫자/영문 (ex. KR1)
    profile_image_url = Column(String(500)) # 페르소나별 독립 프로필 이미지 노출용
    profile_msg = Column(String(200))    
    persona_type = Column(String(50))    
    is_main = Column(SmallInteger, default=0)    
    preference_status = Column(Text)    
    status = Column(String(20), default="ACTIVE") # 'ACTIVE' 또는 'DELETED' 상태 관리
    deleted_at = Column(DateTime, nullable=True) # 삭제 요청 유예 기간(30일) 체크용

    user = relationship("User", back_populates="personas")    
    posts = relationship("Post", back_populates="persona", cascade="all, delete-orphan")    
    comments = relationship("Comment", back_populates="persona", cascade="all, delete-orphan")    
    
    # Follow 관계 (Self-referential N:M)
    following = relationship("Follow", foreign_keys="Follow.follower_id", back_populates="follower", cascade="all, delete-orphan")    
    followers = relationship("Follow", foreign_keys="Follow.following_id", back_populates="following_persona", cascade="all, delete-orphan")    

    __table_args__ = (
        UniqueConstraint('nickname', 'tag', name='uq_persona_nickname_tag'),
    )

class Follow(Base):
    __tablename__ = "follow"
    follower_id = Column(Integer, ForeignKey("persona.id", ondelete="CASCADE"), primary_key=True)    
    following_id = Column(Integer, ForeignKey("persona.id", ondelete="CASCADE"), primary_key=True)    
    created_at = Column(DateTime, server_default=func.now())    

    follower = relationship("Persona", foreign_keys=[follower_id], back_populates="following")    
    following_persona = relationship("Persona", foreign_keys=[following_id], back_populates="followers")    

# --- 3. 게시물 및 영화 정보 테이블 ---

class Post(Base):
    __tablename__ = "post"
    id = Column(Integer, primary_key=True)    
    persona_id = Column(Integer, ForeignKey("persona.id", ondelete="CASCADE"), nullable=False)    
    title = Column(String(255), nullable=False)    
    content = Column(Text)    
    image_urls = Column(JSON) # 최대 5장 이미지 배열 저장용    
    is_spoiler = Column(SmallInteger, default=0) # 0: 일반, 1: 스포일러    
    status = Column(String(20), default="ACTIVE") # ACTIVE, INACTIVE    
    is_analyzed = Column(SmallInteger, default=0)    
    created_at = Column(DateTime, server_default=func.now())    
    updated_at = Column(DateTime, onupdate=func.now())    

    persona = relationship("Persona", back_populates="posts")    
    comments = relationship("Comment", back_populates="post", cascade="all, delete-orphan")    
    movies = relationship("Movie", secondary="post_movie", back_populates="posts")    
    hashtags = relationship("Hashtag", secondary="post_hashtag", back_populates="posts")    
    mentions = relationship("Persona", secondary="post_mention", backref="mentioned_in_posts")    

class Movie(Base):
    __tablename__ = "movie"
    id = Column(Integer, primary_key=True)    
    title = Column(String(255))    
    overview = Column(Text)    
    release_date = Column(DateTime)    
    avg_rating = Column(Numeric(10, 2))    
    poster_url = Column(String(500))    
    
    genres = relationship("Genre", secondary="movie_genre", back_populates="movies")
    posts = relationship("Post", secondary="post_movie", back_populates="movies")
    staff = relationship("People", secondary="movie_staff", back_populates="movies")

class Genre(Base):
    __tablename__ = "genre"
    id = Column(Integer, primary_key=True)    
    name = Column(String(50))    
    
    movies = relationship("Movie", secondary="movie_genre", back_populates="genres")

class People(Base):
    __tablename__ = "people"
    id = Column(Integer, primary_key=True)    
    name = Column(String(50))    
    profile_image = Column(String(500))    
    job = Column(String(30))    

    movies = relationship("Movie", secondary="movie_staff", back_populates="staff")

# --- 4. 활동 로그 및 관계(N:M) 테이블 ---

class Comment(Base):
    __tablename__ = "comment"
    id = Column(Integer, primary_key=True)    
    post_id = Column(Integer, ForeignKey("post.id", ondelete="CASCADE"), nullable=False)    
    persona_id = Column(Integer, ForeignKey("persona.id", ondelete="CASCADE"), nullable=False)    
    parent_id = Column(Integer, ForeignKey("comment.id", ondelete="CASCADE"), nullable=True) # 대댓글용 계층 구조    
    content = Column(String(1000))    
    is_spoiler = Column(SmallInteger, default=0) # 0: 일반, 1: 스포일러    
    status = Column(String(20), default="ACTIVE") # ACTIVE, INACTIVE    
    created_at = Column(DateTime, server_default=func.now())    
    updated_at = Column(DateTime, onupdate=func.now())    
    is_pinned = Column(SmallInteger, default=0)    
    is_analyzed = Column(SmallInteger, default=0)    

    post = relationship("Post", back_populates="comments")    
    persona = relationship("Persona", back_populates="comments")    
    replies = relationship("Comment", back_populates="parent", cascade="all, delete-orphan")    
    parent = relationship("Comment", back_populates="replies", remote_side=[id])    
    mentions = relationship("Persona", secondary="comment_mention", backref="mentioned_in_comments")    

class LikeLog(Base):
    __tablename__ = "like_log"
    id = Column(Integer, primary_key=True, autoincrement=True)    
    persona_id = Column(Integer, ForeignKey("persona.id", ondelete="CASCADE"), nullable=False)    
    target_type = Column(String(20), nullable=False) # 'POST', 'COMMENT' 등    
    target_id = Column(Integer, nullable=False)    
    is_active = Column(SmallInteger, default=1) # 1: 좋아요, 0: 취소됨    
    created_at = Column(DateTime, server_default=func.now())    
    updated_at = Column(DateTime, onupdate=func.now())    

    __table_args__ = (
        UniqueConstraint('persona_id', 'target_type', 'target_id', name='uq_likelog_persona_target'),
        Index('ix_likelog_target', 'target_type', 'target_id'),
    )

class EntityRelationshipLog(Base):
    __tablename__ = "entity_relationship_log"
    id = Column(Integer, primary_key=True)    
    persona_id = Column(Integer, ForeignKey("persona.id", ondelete="CASCADE"), nullable=False)    
    relation_type = Column(String(30))    
    target_type = Column(String(30))    
    target_id = Column(Integer)    
    sentiment_score = Column(Numeric(10, 4))    
    weight = Column(Double)    
    created_at = Column(DateTime, server_default=func.now())    

    __table_args__ = (
        Index('ix_entity_log_target', 'target_type', 'target_id'),
    )

class SemanticAnalysis(Base):
    __tablename__ = "semantic_analysis"
    id = Column(Integer, primary_key=True)    
    target_type = Column(String(30))    
    target_id = Column(Integer)    
    summary = Column(Text)    
    keywords = Column(JSON) # JSON 타입 반영 

    __table_args__ = (
        Index('ix_semantic_target', 'target_type', 'target_id'),
    )

# --- 5. 중간 다리(Link) 테이블들 ---

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
    persona_id = Column(Integer, ForeignKey("persona.id", ondelete="CASCADE"), primary_key=True)    

class CommentMention(Base):
    __tablename__ = "comment_mention"
    comment_id = Column(Integer, ForeignKey("comment.id", ondelete="CASCADE"), primary_key=True)    
    persona_id = Column(Integer, ForeignKey("persona.id", ondelete="CASCADE"), primary_key=True)    

class MovieGenre(Base):
    __tablename__ = "movie_genre"
    movie_id = Column(Integer, ForeignKey("movie.id", ondelete="CASCADE"), primary_key=True)    
    genre_id = Column(Integer, ForeignKey("genre.id", ondelete="CASCADE"), primary_key=True)    

class MovieStaff(Base):
    __tablename__ = "movie_staff"
    movie_id = Column(Integer, ForeignKey("movie.id", ondelete="CASCADE"), primary_key=True)    
    people_id = Column(Integer, ForeignKey("people.id", ondelete="CASCADE"), primary_key=True)    
    job = Column(String(30))    

class FavGenre(Base):
    __tablename__ = "fav_genre"
    persona_id = Column(Integer, ForeignKey("persona.id", ondelete="CASCADE"), primary_key=True)    
    genre_id = Column(Integer, ForeignKey("genre.id", ondelete="CASCADE"), primary_key=True)    

class FavPeople(Base):
    __tablename__ = "fav_people"
    persona_id = Column(Integer, ForeignKey("persona.id", ondelete="CASCADE"), primary_key=True)    
    people_id = Column(Integer, ForeignKey("people.id", ondelete="CASCADE"), primary_key=True)    
    type = Column(String(30))    
