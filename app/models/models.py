from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime, Numeric, SmallInteger, BigInteger, JSON, Double
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base # 프로젝트의 Base 클래스 경로에 맞춰 수정

# --- 1. 인증 및 사용자 관련 테이블 ---

class User(Base):
    __tablename__ = "User"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True) [cite: 1]
    ci_value = Column(String(255), unique=True, nullable=False) [cite: 1]
    username = Column(String(150), nullable=False) [cite: 1]
    phone = Column(String(20), nullable=False) [cite: 1]
    nickname = Column(String(150), nullable=False) [cite: 1]
    created_at = Column(DateTime, server_default=func.now()) [cite: 1]
    updated_at = Column(DateTime, onupdate=func.now()) [cite: 1]

    profiles = relationship("Profile", back_populates="user") [cite: 1]
    local_auths = relationship("LocalAuth", back_populates="user") [cite: 2]
    social_auths = relationship("SocialAuth", back_populates="user") [cite: 2]

class LocalAuth(Base):
    __tablename__ = "local_auth"
    auth_id = Column(BigInteger, primary_key=True, autoincrement=True) [cite: 2]
    user_id = Column(Integer, ForeignKey("User.id"), nullable=False) [cite: 2]
    email = Column(String(100), nullable=False) [cite: 2]
    password_hash = Column(String(255), nullable=False) [cite: 2]
    email_verified = Column(SmallInteger, default=0, nullable=False) [cite: 2]

    user = relationship("User", back_populates="local_auths") [cite: 2]

class SocialAuth(Base):
    __tablename__ = "social_auth"
    social_id = Column(BigInteger, primary_key=True) [cite: 1]
    user_id = Column(Integer, ForeignKey("User.id"), nullable=False) [cite: 2]
    provider = Column(String(20), nullable=False) [cite: 1]
    provider_user_id = Column(String(255), nullable=False) [cite: 2]
    conected_at = Column(DateTime, server_default=func.now()) [cite: 2]

    user = relationship("User", back_populates="social_auths") [cite: 2]

# --- 2. 페르소나(프로필) 및 소셜 기능 테이블 ---

class Profile(Base):
    __tablename__ = "profile"
    id = Column(Integer, primary_key=True, autoincrement=True) [cite: 1]
    user_id = Column(Integer, ForeignKey("User.id"), nullable=False) [cite: 1]
    nickname = Column(String(50)) [cite: 1]
    profile_msg = Column(String(200)) [cite: 1]
    persona_type = Column(String(50)) [cite: 1]
    is_main = Column(SmallInteger) [cite: 1]
    preference_status = Column(Text) [cite: 1]

    user = relationship("User", back_populates="profiles") [cite: 1]
    posts = relationship("Post", back_populates="profile") [cite: 3]
    comments = relationship("Comment", back_populates="profile") [cite: 4]
    # Follow 관계 (Self-referential N:M)
    following = relationship("Follow", foreign_keys="Follow.follower_id", back_populates="follower") [cite: 3]
    followers = relationship("Follow", foreign_keys="Follow.following_id", back_populates="following_user") [cite: 3]

class Follow(Base):
    __tablename__ = "follow"
    follower_id = Column(Integer, ForeignKey("profile.id"), primary_key=True) [cite: 3]
    following_id = Column(Integer, ForeignKey("profile.id"), primary_key=True) [cite: 3]
    created_at = Column(DateTime, server_default=func.now()) [cite: 3]

    follower = relationship("Profile", foreign_keys=[follower_id], back_populates="following") [cite: 3]
    following_user = relationship("Profile", foreign_keys=[following_id], back_populates="followers") [cite: 3]

# --- 3. 게시물 및 영화 정보 테이블 ---

class Post(Base):
    __tablename__ = "post"
    id = Column(Integer, primary_key=True) [cite: 3]
    profile_id = Column(Integer, ForeignKey("profile.id"), nullable=False) [cite: 3]
    content = Column(Text) [cite: 3]
    image_url = Column(String(500)) [cite: 3]
    is_analyzed = Column(SmallInteger, default=0) [cite: 3]
    created_at = Column(DateTime, server_default=func.now()) [cite: 3]

    profile = relationship("Profile", back_populates="posts") [cite: 3]
    comments = relationship("Comment", back_populates="post") [cite: 4]

class Movie(Base):
    __tablename__ = "movie"
    id = Column(Integer, primary_key=True) [cite: 2]
    title = Column(String(255)) [cite: 2]
    overview = Column(Text) [cite: 2]
    release_date = Column(DateTime) [cite: 2]
    avg_rating = Column(Numeric(10, 0)) [cite: 2]
    poster_url = Column(String(500)) [cite: 2]

class Genre(Base):
    __tablename__ = "genre"
    id = Column(Integer, primary_key=True) [cite: 2]
    name = Column(String(50)) [cite: 2]

class People(Base):
    __tablename__ = "people"
    id = Column(Integer, primary_key=True) [cite: 3]
    name = Column(String(50)) [cite: 3]
    profile_image = Column(String(500)) [cite: 3]
    job = Column(String(30)) [cite: 3]

# --- 4. 활동 로그 및 관계(N:M) 테이블 ---

class Comment(Base):
    __tablename__ = "comment"
    id = Column(Integer, primary_key=True) [cite: 4]
    post_id = Column(Integer, ForeignKey("post.id"), nullable=False) [cite: 4]
    profile_id = Column(Integer, ForeignKey("profile.id"), nullable=False) [cite: 4]
    content = Column(String(1000)) [cite: 4]
    created_at = Column(DateTime, server_default=func.now()) [cite: 4]
    is_pinned = Column(SmallInteger) [cite: 4]
    is_analyzed = Column(SmallInteger, default=0) [cite: 4]

    post = relationship("Post", back_populates="comments") [cite: 4]
    profile = relationship("Profile", back_populates="comments") [cite: 4]

class InteractionLike(Base): # ERD 상의 'like' 테이블
    __tablename__ = "interaction"
    post_id = Column(Integer, ForeignKey("post.id"), primary_key=True) [cite: 4]
    profile_id = Column(Integer, ForeignKey("profile.id"), primary_key=True) [cite: 4]
    created_at = Column(DateTime, server_default=func.now()) [cite: 4]
    is_analyzed = Column(SmallInteger, default=0) [cite: 4]

class CommentLike(Base):
    __tablename__ = "comment_like"
    coment_id = Column(Integer, ForeignKey("comment.id"), primary_key=True) [cite: 5]
    profile_id = Column(Integer, ForeignKey("profile.id"), primary_key=True) [cite: 5]
    created_at = Column(DateTime) [cite: 5]

class EntityRelationshipLog(Base):
    __tablename__ = "entity_relationship_log"
    id = Column(Integer, primary_key=True) [cite: 4]
    profile_id = Column(Integer, ForeignKey("profile.id"), nullable=False) [cite: 4]
    relation_type = Column(String(30)) [cite: 4]
    target_type = Column(String(30)) [cite: 4]
    target_id = Column(Integer) [cite: 4]
    sentiment_score = Column(Numeric(10, 0)) [cite: 4]
    weight = Column(Double) [cite: 4]
    created_at = Column(DateTime, server_default=func.now()) [cite: 4]

class SemanticAnalysis(Base):
    __tablename__ = "Semantic_Analysis"
    id = Column(Integer, primary_key=True) [cite: 5]
    target_type = Column(String(30)) [cite: 5]
    target_id = Column(Integer) [cite: 5]
    summary = Column(Text) [cite: 5]
    keywords = Column(JSON) # JSON 타입 반영 

# --- 5. 중간 다리(Link) 테이블들 ---

class MovieGenre(Base):
    __tablename__ = "movie_genre"
    movie_id = Column(Integer, ForeignKey("movie.id"), primary_key=True) [cite: 3]
    genre_id = Column(Integer, ForeignKey("genre.id"), primary_key=True) [cite: 3]

class MovieStaff(Base):
    __tablename__ = "movie_staff"
    movie_id = Column(Integer, ForeignKey("movie.id"), primary_key=True) [cite: 3]
    people_id = Column(Integer, ForeignKey("people.id"), primary_key=True) [cite: 3]
    job = Column(String(30)) [cite: 3]

class FavGenre(Base):
    __tablename__ = "fav_genre"
    profile_id = Column(Integer, ForeignKey("profile.id"), primary_key=True) [cite: 4]
    genre_id = Column(Integer, ForeignKey("genre.id"), primary_key=True) [cite: 4]

class FavPeople(Base):
    __tablename__ = "fav_people"
    profile_id = Column(Integer, ForeignKey("profile.id"), primary_key=True) [cite: 4]
    people_id = Column(Integer, ForeignKey("people.id"), primary_key=True) [cite: 4]
    type = Column(String(30)) [cite: 4]

class PostMovie(Base):
    __tablename__ = "post_movie"
    post_id = Column(Integer, ForeignKey("post.id"), primary_key=True) [cite: 4]
    movie_id = Column(Integer, ForeignKey("movie.id"), primary_key=True) [cite: 4]