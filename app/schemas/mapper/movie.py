from app.models.movie import Movie as MovieModel
from app.schemas.base.movie import Movie, MovieWithTrailers
from app.schemas.mapper.youtube_video import YoutubeVideoMapper


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

    @staticmethod
    def to_movie_with_trailers(movie: MovieModel) -> MovieWithTrailers:
        base = MovieMapper.to_movie(movie)
        return MovieWithTrailers(
            **base.model_dump(),
            youtube_videos=[
                YoutubeVideoMapper.to_youtube_video(v)
                for v in (movie.youtube_videos or [])
                if v.is_trailer
            ],
        )
