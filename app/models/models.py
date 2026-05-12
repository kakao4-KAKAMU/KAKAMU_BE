from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime, Numeric, SmallInteger, BigInteger, JSON, Double
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base # 프로젝트의 Base 클래스 경로에 맞춰 수정

# --- 1. 인증 및 사용자 관련 테이블 ---

class User(Base):
    __tablename__ = "user"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)    
    ci_value = Column(String(255), unique=True, nullable=False)    
    username = Column(String(150), nullable=False)    
    phone = Column(String(20), nullable=False)    
    nickname = Column(String(150), nullable=False)    
    created_at = Column(DateTime, server_default=func.now())    
    updated_at = Column(DateTime, onupdate=func.now())    

    profiles = relationship("Profile", back_populates="user", cascade="all, delete-orphan")    
    local_auths = relationship("LocalAuth", back_populates="user", cascade="all, delete-orphan")    
    social_auths = relationship("SocialAuth", back_populates="user", cascade="all, delete-orphan")    

class LocalAuth(Base):
    __tablename__ = "local_auth"
    auth_id = Column(BigInteger, primary_key=True, autoincrement=True)    
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False)    
    email = Column(String(100), nullable=False)    
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

# --- 2. 페르소나(프로필) 및 소셜 기능 테이블 ---

class Profile(Base):
    __tablename__ = "profile"
    id = Column(Integer, primary_key=True, autoincrement=True)    
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False)    
    nickname = Column(String(50))    
    profile_msg = Column(String(200))    
    persona_type = Column(String(50))    
    is_main = Column(SmallInteger, default=0)    
    preference_status = Column(Text)    

    user = relationship("User", back_populates="profiles")    
    posts = relationship("Post", back_populates="profile", cascade="all, delete-orphan")    
    comments = relationship("Comment", back_populates="profile", cascade="all, delete-orphan")    
    
    # Follow 관계 (Self-referential N:M)
    following = relationship("Follow", foreign_keys="Follow.follower_id", back_populates="follower", cascade="all, delete-orphan")    
    followers = relationship("Follow", foreign_keys="Follow.following_id", back_populates="following_user", cascade="all, delete-orphan")    

class Follow(Base):
    __tablename__ = "follow"
    follower_id = Column(Integer, ForeignKey("profile.id", ondelete="CASCADE"), primary_key=True)    
    following_id = Column(Integer, ForeignKey("profile.id", ondelete="CASCADE"), primary_key=True)    
    created_at = Column(DateTime, server_default=func.now())    

    follower = relationship("Profile", foreign_keys=[follower_id], back_populates="following")    
    following_user = relationship("Profile", foreign_keys=[following_id], back_populates="followers")    

# --- 3. 게시물 및 영화 정보 테이블 ---

class Post(Base):
    __tablename__ = "post"
    id = Column(Integer, primary_key=True)    
    profile_id = Column(Integer, ForeignKey("profile.id", ondelete="CASCADE"), nullable=False)    
    movie_id = Column(Integer, ForeignKey("movie.id", ondelete="CASCADE"))
    content = Column(Text)    
    image_url = Column(String(500))    
    is_analyzed = Column(SmallInteger, default=0)    
    created_at = Column(DateTime, server_default=func.now())    

    profile = relationship("Profile", back_populates="posts")    
    comments = relationship("Comment", back_populates="post", cascade="all, delete-orphan")    
    movie = relationship("Movie", back_populates="posts")

class Movie(Base):
    __tablename__ = "movie"
    id = Column(Integer, primary_key=True)    
    title = Column(String(255))    
    overview = Column(Text)    
    release_date = Column(DateTime)    
    avg_rating = Column(Numeric(10, 2))    
    poster_url = Column(String(500))    
    
    genres = relationship("Genre", secondary="movie_genre", back_populates="movies")
    posts = relationship("Post", back_populates="movie", cascade="all, delete-orphan")
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
    profile_id = Column(Integer, ForeignKey("profile.id", ondelete="CASCADE"), nullable=False)    
    content = Column(String(1000))    
    created_at = Column(DateTime, server_default=func.now())    
    is_pinned = Column(SmallInteger, default=0)    
    is_analyzed = Column(SmallInteger, default=0)    

    post = relationship("Post", back_populates="comments")    
    profile = relationship("Profile", back_populates="comments")    

class InteractionLike(Base): # ERD 상의 'like' 테이블
    __tablename__ = "interaction"
    post_id = Column(Integer, ForeignKey("post.id", ondelete="CASCADE"), primary_key=True)    
    profile_id = Column(Integer, ForeignKey("profile.id", ondelete="CASCADE"), primary_key=True)    
    created_at = Column(DateTime, server_default=func.now())    
    is_analyzed = Column(SmallInteger, default=0)    

class CommentLike(Base):
    __tablename__ = "comment_like"
    comment_id = Column(Integer, ForeignKey("comment.id", ondelete="CASCADE"), primary_key=True)    
    profile_id = Column(Integer, ForeignKey("profile.id", ondelete="CASCADE"), primary_key=True)    
    created_at = Column(DateTime, server_default=func.now())    

class EntityRelationshipLog(Base):
    __tablename__ = "entity_relationship_log"
    id = Column(Integer, primary_key=True)    
    profile_id = Column(Integer, ForeignKey("profile.id", ondelete="CASCADE"), nullable=False)    
    relation_type = Column(String(30))    
    target_type = Column(String(30))    
    target_id = Column(Integer)    
    sentiment_score = Column(Numeric(10, 4))    
    weight = Column(Double)    
    created_at = Column(DateTime, server_default=func.now())    

class SemanticAnalysis(Base):
    __tablename__ = "semantic_analysis"
    id = Column(Integer, primary_key=True)    
    target_type = Column(String(30))    
    target_id = Column(Integer)    
    summary = Column(Text)    
    keywords = Column(JSON) # JSON 타입 반영 

# --- 5. 중간 다리(Link) 테이블들 ---

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
    profile_id = Column(Integer, ForeignKey("profile.id", ondelete="CASCADE"), primary_key=True)    
    genre_id = Column(Integer, ForeignKey("genre.id", ondelete="CASCADE"), primary_key=True)    

class FavPeople(Base):
    __tablename__ = "fav_people"
    profile_id = Column(Integer, ForeignKey("profile.id", ondelete="CASCADE"), primary_key=True)    
    people_id = Column(Integer, ForeignKey("people.id", ondelete="CASCADE"), primary_key=True)    
    type = Column(String(30))    
