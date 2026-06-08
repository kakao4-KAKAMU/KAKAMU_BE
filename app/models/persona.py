import uuid
from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime, SmallInteger, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base import Base

class Persona(Base):
    __tablename__ = "persona"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)    
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.id", ondelete="CASCADE"), nullable=False)    
    nickname = Column(String(50), nullable=False) # 내부 관리/식별용 이름
    profile_image_url = Column(String(500)) 
    persona_type = Column(String(50))      
    status = Column(String(20), default="ACTIVE") 
    deleted_at = Column(DateTime, nullable=True) 

    user = relationship("User", back_populates="personas")    

    # 선호 취향 매핑 테이블들과의 관계 설정
    fav_genres = relationship("FavGenre", cascade="all, delete-orphan")
    fav_people = relationship("FavPeople", cascade="all, delete-orphan")
    fav_movies = relationship("FavMovie", cascade="all, delete-orphan")

class FavGenre(Base):
    __tablename__ = "fav_genre"
    persona_id = Column(UUID(as_uuid=True), ForeignKey("persona.id", ondelete="CASCADE"), primary_key=True)    
    genre_id = Column(Integer, ForeignKey("genre.id", ondelete="CASCADE"), primary_key=True)    

class FavPeople(Base):
    __tablename__ = "fav_people"
    persona_id = Column(UUID(as_uuid=True), ForeignKey("persona.id", ondelete="CASCADE"), primary_key=True)    
    people_id = Column(Integer, ForeignKey("people.id", ondelete="CASCADE"), primary_key=True)    
    type = Column(String(30))    

class FavMovie(Base):
    __tablename__ = "fav_movie"
    persona_id = Column(UUID(as_uuid=True), ForeignKey("persona.id", ondelete="CASCADE"), primary_key=True)    
    movie_id = Column(Integer, ForeignKey("movie.id", ondelete="CASCADE"), primary_key=True)    