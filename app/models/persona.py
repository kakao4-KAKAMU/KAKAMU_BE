from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime, SmallInteger, UniqueConstraint
from sqlalchemy.orm import relationship
from app.db.base import Base

class Persona(Base):
    __tablename__ = "persona"
    id = Column(Integer, primary_key=True, autoincrement=True)    
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False)    
    nickname = Column(String(50), nullable=False) 
    tag = Column(String(10), nullable=False) 
    profile_image_url = Column(String(500)) 
    profile_msg = Column(String(200))    
    persona_type = Column(String(50))    
    is_main = Column(SmallInteger, default=0)    
    preference_status = Column(Text)    
    status = Column(String(20), default="ACTIVE") 
    deleted_at = Column(DateTime, nullable=True) 

    user = relationship("User", back_populates="personas")    
    posts = relationship("Post", back_populates="persona", cascade="all, delete-orphan")    
    comments = relationship("Comment", back_populates="persona", cascade="all, delete-orphan")    
    
    following = relationship("Follow", foreign_keys="Follow.follower_id", back_populates="follower", cascade="all, delete-orphan")    
    followers = relationship("Follow", foreign_keys="Follow.following_id", back_populates="following_persona", cascade="all, delete-orphan")    

    __table_args__ = (
        UniqueConstraint('nickname', 'tag', name='uq_persona_nickname_tag'),
    )

class FavGenre(Base):
    __tablename__ = "fav_genre"
    persona_id = Column(Integer, ForeignKey("persona.id", ondelete="CASCADE"), primary_key=True)    
    genre_id = Column(Integer, ForeignKey("genre.id", ondelete="CASCADE"), primary_key=True)    

class FavPeople(Base):
    __tablename__ = "fav_people"
    persona_id = Column(Integer, ForeignKey("persona.id", ondelete="CASCADE"), primary_key=True)    
    people_id = Column(Integer, ForeignKey("people.id", ondelete="CASCADE"), primary_key=True)    
    type = Column(String(30))    