from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime, JSON, SmallInteger
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base

class Post(Base):
    __tablename__ = "post"
    id = Column(Integer, primary_key=True)    
    persona_id = Column(UUID(as_uuid=True), ForeignKey("persona.id", ondelete="CASCADE"), nullable=False)    
    title = Column(String(255), nullable=False)    
    content = Column(Text)    
    image_urls = Column(JSON) 
    is_spoiler = Column(SmallInteger, default=0) 
    status = Column(String(20), default="ACTIVE") 
    is_analyzed = Column(SmallInteger, default=0)    
    created_at = Column(DateTime, server_default=func.now())    
    updated_at = Column(DateTime, onupdate=func.now())    

    persona = relationship("Persona", back_populates="posts")    
    comments = relationship("Comment", back_populates="post", cascade="all, delete-orphan")    
    movies = relationship("Movie", secondary="post_movie", back_populates="posts")    
    hashtags = relationship("Hashtag", secondary="post_hashtag", back_populates="posts")    
    mentions = relationship("Persona", secondary="post_mention", backref="mentioned_in_posts")    

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
    persona_id = Column(UUID(as_uuid=True), ForeignKey("persona.id", ondelete="CASCADE"), primary_key=True)    