from app.models.movie import Movie as MovieModel
from app.schemas.base.movie import Movie


class MovieMapper:
    @staticmethod
    def to_movie(movie: MovieModel) -> Movie:
        title = movie.titles[0].title_name if movie.titles else "제목 없음"
        return Movie(
            id=movie.id,
            title=title,
            release_date=movie.release_date,
            poster_url=movie.poster_url,
        )
