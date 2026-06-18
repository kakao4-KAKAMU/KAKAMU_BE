from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import and_, extract
from sqlalchemy.orm import Query, Session, selectinload

from app.models.movie import Genre, Movie, MovieTitle


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


movie_read_service = MovieReadService()
