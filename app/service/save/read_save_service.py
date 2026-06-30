from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session, selectinload

from app.models import Movie, SaveLog
from app.schemas.mapper.movie import MovieMapper
from app.schemas.response.save import SavedMovieListResponse
from app.service.movie.get_movie import movie_read_service


class SaveReadService:
    def get_my_saved_movies(
        self,
        db: Session,
        current_user_id: UUID,
        cursor: Optional[int],
        limit: int,
    ) -> SavedMovieListResponse:
        """내가 저장한 영화 목록 조회"""
        query = db.query(SaveLog).filter(
            SaveLog.user_id == current_user_id,
            SaveLog.target_type == "MOVIE",
            SaveLog.is_active == 1,
        ).order_by(SaveLog.id.desc())

        if cursor:
            query = query.filter(SaveLog.id < cursor)

        save_logs = query.limit(limit + 1).all()
        has_next = len(save_logs) > limit
        save_logs = save_logs[:limit]

        if not save_logs:
            return SavedMovieListResponse(items=[], next_cursor=None, has_next=False)

        movie_ids = [log.movie_id for log in save_logs]
        movies = (
            movie_read_service.base_query(db)
            .filter(Movie.id.in_(movie_ids))
            .options(selectinload(Movie.titles))
            .all()
        )
        movies_by_id = {movie.id: movie for movie in movies}
        ordered_movies = [movies_by_id[movie_id] for movie_id in movie_ids if movie_id in movies_by_id]

        return SavedMovieListResponse(
            items=[MovieMapper.to_movie(movie) for movie in ordered_movies],
            next_cursor=save_logs[-1].id if has_next else None,
            has_next=has_next,
        )


save_read_service = SaveReadService()
