import uuid
from sqlalchemy import Column, Integer, ForeignKey, Text, Index, Boolean, DateTime, String, text
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base import Base

class MovieType(Base):
    __tablename__ = "movie_type"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    type = Column(Text, nullable=False)

    movies = relationship("Movie", back_populates="movie_type")

class Movie(Base):
    __tablename__ = "movie"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    poster_url = Column(Text)
    nation = Column(Text)
    release_date = Column(Text)
    kmdb_id = Column(Text)
    tmdb_id = Column(Text, comment='TMDB ID')
    producing_year = Column(Integer, comment='producing year')
    movie_type_id = Column(UUID(as_uuid=True), ForeignKey('movie_type.id'), comment='movie type id')
    runtime = Column(Integer, comment='runtime integer')
    is_adult = Column(Boolean, comment='19세 이상 관람 가능 여부')
    is_rated = Column(Boolean, comment='심의 데이터 보유 여부')
    
    movie_type = relationship("MovieType", back_populates="movies")
    genres = relationship("Genre", secondary="movie_genre_relation", back_populates="movies")
    posts = relationship("Post", secondary="post_movie", back_populates="movies")
    staff = relationship("People", secondary="movie_person_relation", back_populates="movies")
    titles = relationship("MovieTitle", back_populates="movie")
    original_title = relationship(
        "MovieOriginalTitle",
        back_populates="movie",
        uselist=False,
        viewonly=True,
    )
    overviews = relationship("Overview", back_populates="movie")
    youtube_videos = relationship("YoutubeVideo", back_populates="movie")

class Overview(Base):
    __tablename__ = "overview"
    movie_id = Column(UUID(as_uuid=True), ForeignKey('movie.id'), primary_key=True, nullable=False)
    platform = Column(Text, primary_key=True, nullable=False)
    lang = Column(Text, primary_key=True)
    overview = Column(Text, nullable=False)

    movie = relationship("Movie", back_populates="overviews")

class YoutubeVideo(Base):
    __tablename__ = "youtube_video"
    movie_id = Column(UUID(as_uuid=True), ForeignKey('movie.id'), primary_key=True, nullable=False)
    is_trailer = Column(Boolean, nullable=False)
    language = Column(Text, nullable=False)
    youtube_video_id = Column(Text, primary_key=True, nullable=False)

    movie = relationship("Movie", back_populates="youtube_videos")

class Genre(Base):
    __tablename__ = "genre"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    genre_name = Column(Text, nullable=False)
    
    movies = relationship("Movie", secondary="movie_genre_relation", back_populates="genres")

class People(Base):
    __tablename__ = "person"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    person_name = Column(Text)
    person_name_eng = Column(Text)
    kmdb_person_id = Column(Text)

    movies = relationship("Movie", secondary="movie_person_relation", back_populates="staff")

    __table_args__ = (
        Index('ix_people_name_trgm', 'person_name', postgresql_using='gin', postgresql_ops={'person_name': 'gin_trgm_ops'}),
    )

class MovieGenre(Base):
    __tablename__ = "movie_genre_relation"
    movie_id = Column(UUID(as_uuid=True), ForeignKey("movie.id", ondelete="CASCADE"), primary_key=True)
    genre_id = Column(UUID(as_uuid=True), ForeignKey("genre.id", ondelete="CASCADE"), primary_key=True)

class MovieStaff(Base):
    __tablename__ = "movie_person_relation"
    movie_id = Column(UUID(as_uuid=True), ForeignKey("movie.id", ondelete="CASCADE"), primary_key=True)
    people_id = Column("person_id", UUID(as_uuid=True), ForeignKey("person.id", ondelete="CASCADE"), primary_key=True)
    job = Column(Text, primary_key=True, nullable=False)

class MovieOriginalTitle(Base):
    __tablename__ = "movie_original_title"

    movie_id = Column(UUID(as_uuid=True), ForeignKey("movie.id"), primary_key=True)
    title_name = Column(Text, nullable=False)

    movie = relationship("Movie", back_populates="original_title", viewonly=True)


class MovieTitle(Base):
    __tablename__ = "movie_title"
    movie_id = Column(UUID(as_uuid=True), ForeignKey("movie.id", ondelete="CASCADE"), primary_key=True)
    title_name = Column(Text, primary_key=True, nullable=False)
    country = Column(Text, primary_key=True, nullable=False)
    is_original = Column(Boolean, primary_key=True, nullable=False)

    movie = relationship("Movie", back_populates="titles")

    __table_args__ = (
        Index('ix_movie_title_trgm', 'title_name', postgresql_using='gin', postgresql_ops={'title_name': 'gin_trgm_ops'}),
    )

class MovieEvaluation(Base):
    __tablename__ = "movie_evaluation"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    persona_id = Column(UUID(as_uuid=True), ForeignKey("persona.id", ondelete="CASCADE"), nullable=True)
    movie_id = Column(UUID(as_uuid=True), ForeignKey("movie.id", ondelete="CASCADE"), nullable=False)
    evaluation = Column(String(20), nullable=False)  # "LIKE" or "DISLIKE"
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User")
    persona = relationship("Persona")
    movie = relationship("Movie")

    __table_args__ = (
        Index(
            "uq_movie_evaluation_persona_movie",
            "persona_id",
            "movie_id",
            unique=True,
            postgresql_where=text("persona_id IS NOT NULL"),
        ),
        Index(
            "uq_movie_evaluation_user_movie",
            "user_id",
            "movie_id",
            unique=True,
            postgresql_where=text("persona_id IS NULL"),
        ),
    )