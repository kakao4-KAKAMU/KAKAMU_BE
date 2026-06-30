from app.models.movie import (
    Movie as MovieModel,
    MovieTitle as MovieTitleModel,
    Overview as OverviewModel,
    People,
)
from app.schemas.base.movie import Movie, MovieDetail, MovieTitle, MovieWithTrailers, Overview
from app.schemas.mapper.genre import GenreMapper
from app.schemas.mapper.person import PersonMapper
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

    @staticmethod
    def to_movie_title(title: MovieTitleModel) -> MovieTitle:
        return MovieTitle(
            title_name=title.title_name,
            country=title.country,
            is_original=title.is_original,
        )

    @staticmethod
    def to_overview(overview: OverviewModel) -> Overview:
        return Overview(
            platform=overview.platform,
            lang=overview.lang,
            overview=overview.overview,
        )

    @staticmethod
    def to_movie_detail(
        movie: MovieModel,
        *,
        staffs: list[tuple[People, str]],
        is_saved: bool = False,
    ) -> MovieDetail:
        return MovieDetail(
            id=movie.id,
            titles=[MovieMapper.to_movie_title(title) for title in (movie.titles or [])],
            poster_url=movie.poster_url,
            nation=movie.nation,
            release_date=movie.release_date,
            producing_year=movie.producing_year,
            runtime=movie.runtime,
            is_adult=bool(movie.is_adult),
            youtube_videos=[
                YoutubeVideoMapper.to_youtube_video(video)
                for video in (movie.youtube_videos or [])
            ],
            overviews=[MovieMapper.to_overview(overview) for overview in (movie.overviews or [])],
            genres=[GenreMapper.to_genre(genre) for genre in (movie.genres or [])],
            staffs=[
                PersonMapper.to_person(person, job=job)
                for person, job in staffs
            ],
            is_saved=is_saved,
        )
