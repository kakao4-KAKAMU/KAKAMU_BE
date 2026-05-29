from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime, Numeric, Index
from sqlalchemy.orm import relationship
from app.db.base import Base

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

    __table_args__ = (
        Index('ix_movie_title_trgm', 'title', postgresql_using='gin', postgresql_ops={'title': 'gin_trgm_ops'}),
    )

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

    __table_args__ = (
        Index('ix_people_name_trgm', 'name', postgresql_using='gin', postgresql_ops={'name': 'gin_trgm_ops'}),
    )

class MovieGenre(Base):
    __tablename__ = "movie_genre"
    movie_id = Column(Integer, ForeignKey("movie.id", ondelete="CASCADE"), primary_key=True)    
    genre_id = Column(Integer, ForeignKey("genre.id", ondelete="CASCADE"), primary_key=True)    

class MovieStaff(Base):
    __tablename__ = "movie_staff"
    movie_id = Column(Integer, ForeignKey("movie.id", ondelete="CASCADE"), primary_key=True)    
    people_id = Column(Integer, ForeignKey("people.id", ondelete="CASCADE"), primary_key=True)    
    job = Column(String(30))    