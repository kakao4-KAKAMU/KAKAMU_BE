from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import and_, extract
from sqlalchemy.orm import Query, Session, selectinload

from app.models.movie import Genre, Movie, MovieTitle
from app.schemas.base.movie import Movie as MovieSchema
from app.schemas.response.search import MovieFilterSearchResponse, MovieTabSearchResponse
from app.schemas.mapper.movie import MovieMapper
from app.schemas.mapper.pagination import PaginationMapper


class MovieReadService:
    """영화 조회 서비스.

    기본 Movie 조회 조건:
    - is_rated = True
    - is_adult = False
    - producing_year IS NOT NULL
    - tmdb_id IS NOT NULL
    """

    @staticmethod
    def apply_base_filter(query: Query) -> Query:
        return query.filter(
            Movie.is_rated.is_(True),
            Movie.is_adult.is_(False),
            Movie.producing_year.isnot(None),
            Movie.tmdb_id.isnot(None),
        )

    def base_query(self, db: Session) -> Query:
        return self.apply_base_filter(db.query(Movie))

    def search_content_tab(
        self,
        db: Session,
        search_pattern: str,
        *,
        sort: str = "accuracy",
        cursor: Optional[str] = None,
        limit: int = 20,
    ) -> List[Movie]:
        query = self.base_query(db).filter(
            Movie.titles.any(MovieTitle.title_name.ilike(search_pattern))
        )

        if sort == "popularity":
            query = query.order_by(Movie.producing_year.desc().nullslast(), Movie.id.desc())
        elif sort == "latest":
            query = query.order_by(Movie.release_date.desc().nullslast(), Movie.id.desc())
        elif sort in ("name_asc", "name_desc"):
            query = query.outerjoin(
                MovieTitle, and_(Movie.id == MovieTitle.movie_id, MovieTitle.is_original)
            )
            if sort == "name_asc":
                query = query.order_by(MovieTitle.title_name.asc(), Movie.id.desc())
            else:
                query = query.order_by(MovieTitle.title_name.desc(), Movie.id.desc())
        else:
            if cursor:
                query = query.filter(Movie.id < cursor)
            query = query.order_by(Movie.id.desc())

        return query.options(selectinload(Movie.titles)).limit(limit).all()

    def search_content_tab_response(
        self,
        db: Session,
        search_pattern: str,
        *,
        sort: str = "accuracy",
        cursor: Optional[str] = None,
        limit: int = 20,
    ) -> MovieTabSearchResponse:
        movies = self.search_content_tab(
            db,
            search_pattern,
            sort=sort,
            cursor=cursor,
            limit=limit,
        )
        next_cursor = movies[-1].id if len(movies) == limit and sort == "accuracy" else None
        return MovieTabSearchResponse(
            items=[MovieMapper.to_movie(movie) for movie in movies],
            meta=PaginationMapper.build_cursor_meta(
                next_cursor=next_cursor,
                has_next=next_cursor is not None,
            ),
        )

    def search_movies_response(
        self,
        db: Session,
        *,
        search_pattern: Optional[str] = None,
        genre: Optional[List[UUID]] = None,
        year: Optional[int] = None,
        sort: str = "year_desc",
        skip: int = 0,
        limit: int = 20,
    ) -> MovieFilterSearchResponse:
        movies, total_count = self.search_movies(
            db,
            search_pattern=search_pattern,
            genre=genre,
            year=year,
            sort=sort,
            skip=skip,
            limit=limit,
        )
        return MovieFilterSearchResponse(
            items=[MovieMapper.to_movie(movie) for movie in movies],
            skip=skip,
            limit=limit,
            total_count=total_count,
        )

    def search_movies(
        self,
        db: Session,
        *,
        search_pattern: Optional[str] = None,
        genre: Optional[List[UUID]] = None,
        year: Optional[int] = None,
        sort: str = "year_desc",
        skip: int = 0,
        limit: int = 20,
    ) -> Tuple[List[Movie], int]:
        query = self.base_query(db).options(selectinload(Movie.titles))

        if search_pattern:
            query = query.filter(
                Movie.titles.any(MovieTitle.title_name.ilike(search_pattern))
            )
        if year:
            query = query.filter(extract("year", Movie.release_date) == year)
        if genre:
            query = query.join(Movie.genres).filter(Genre.id.in_(genre))

        if sort in ("name_asc", "name_desc"):
            query = query.outerjoin(
                MovieTitle, and_(Movie.id == MovieTitle.movie_id, MovieTitle.is_original)
            )
            if sort == "name_asc":
                query = query.order_by(MovieTitle.title_name.asc(), Movie.id.desc())
            else:
                query = query.order_by(MovieTitle.title_name.desc(), Movie.id.desc())
        elif sort == "year_asc":
            query = query.order_by(Movie.release_date.asc().nullslast(), Movie.id.desc())
        else:
            query = query.order_by(Movie.release_date.desc().nullslast(), Movie.id.desc())

        total_count = query.count()
        movies = query.offset(skip).limit(limit).all()
        return movies, total_count

    def get_movies_by_ids(self, db: Session, movie_ids: list[UUID]) -> list[MovieSchema]:
        if not movie_ids:
            return []

        unique_ids = list(dict.fromkeys(movie_ids))
        movies = (
            self.base_query(db)
            .filter(Movie.id.in_(unique_ids))
            .all()
        )
        movies_by_id = {str(movie.id): movie for movie in movies}
        return [
            MovieMapper.to_movie(movies_by_id[str(movie_id)])
            for movie_id in movie_ids
            if str(movie_id) in movies_by_id
        ]


movie_read_service = MovieReadService()
