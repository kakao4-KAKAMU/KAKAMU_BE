import enum
import uuid
from sqlalchemy import Column, String, ForeignKey, DateTime, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base import Base


class PersonaStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    DELETED = "DELETED"


class Persona(Base):
    __tablename__ = "persona"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)    
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.id", ondelete="CASCADE"), nullable=False)    
    nickname = Column(String(50), nullable=False) # 내부 관리/식별용 이름
    profile_image_url = Column(String(500)) 
    persona_type = Column(String(50))      
    status = Column(Enum(PersonaStatus), default=PersonaStatus.ACTIVE, nullable=False)
    deleted_at = Column(DateTime, nullable=True) 

    user = relationship("User", back_populates="personas")    

    # 선호 취향 매핑 테이블들과의 관계 설정
    fav_genres = relationship("FavGenre", cascade="all, delete-orphan")
    fav_people = relationship("FavPeople", cascade="all, delete-orphan")
    fav_movies = relationship("FavMovie", cascade="all, delete-orphan")

class FavGenre(Base):
    __tablename__ = "fav_genre"
    persona_id = Column(UUID(as_uuid=True), ForeignKey("persona.id", ondelete="CASCADE"), primary_key=True)    
    genre_id = Column(UUID(as_uuid=True), ForeignKey("genre.id", ondelete="CASCADE"), primary_key=True)

    genre = relationship("Genre")

class FavPeople(Base):
    __tablename__ = "fav_people"
    persona_id = Column(UUID(as_uuid=True), ForeignKey("persona.id", ondelete="CASCADE"), primary_key=True)    
    people_id = Column(UUID(as_uuid=True), ForeignKey("person.id", ondelete="CASCADE"), primary_key=True)    
    type = Column(String(30))

    person = relationship("People")

class FavMovie(Base):
    __tablename__ = "fav_movie"
    persona_id = Column(UUID(as_uuid=True), ForeignKey("persona.id", ondelete="CASCADE"), primary_key=True)    
    movie_id = Column(UUID(as_uuid=True), ForeignKey("movie.id", ondelete="CASCADE"), primary_key=True)

    movie = relationship("Movie")