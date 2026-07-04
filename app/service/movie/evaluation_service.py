from typing import Literal, Optional, Set
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session, selectinload

from app.models import MovieEvaluation, Persona, User, PersonaStatus
from app.models.movie import Movie, YoutubeVideo
from app.schemas.errors import (
    ERROR_ALREADY_EVALUATED,
    ERROR_MOVIE_NOT_FOUND,
    ERROR_PERSONA_NOT_FOUND_OR_FORBIDDEN,
)
from app.schemas.mapper.movie import MovieMapper
from app.schemas.mapper.persona import PersonaMapper
from app.schemas.response.movie_analyzer import (
    MovieEvaluationItem,
    MovieEvaluationListResponse,
    MovieEvaluationResponse,
    MovieToEvaluateListResponse,
)
from app.service.ml.sync import safe_ml_call
from app.service.movie.evaluation_ml_sync import movie_evaluation_ml_sync_service
from app.service.movie.get_movie import movie_read_service
from app.service.movie.recommendation import movie_recommendation_service


def _error_detail(error_schema: dict) -> dict:
    return error_schema["content"]["application/json"]["example"]["detail"]


class MovieEvaluationService:
    def _verify_persona_ownership(
        self, db: Session, persona_id: UUID, current_user: User
    ) -> Persona:
        persona = db.get(Persona, persona_id)
        if not persona or persona.user_id != current_user.id or persona.status == PersonaStatus.DELETED:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=_error_detail(ERROR_PERSONA_NOT_FOUND_OR_FORBIDDEN),
            )
        return persona

    def _get_evaluated_movie_ids(
        self,
        db: Session,
        user: User,
        persona_id: Optional[UUID],
    ) -> Set[UUID]:
        if persona_id:
            rows = (
                db.query(MovieEvaluation.movie_id)
                .filter(MovieEvaluation.persona_id == persona_id)
                .all()
            )
        else:
            rows = (
                db.query(MovieEvaluation.movie_id)
                .filter(
                    MovieEvaluation.user_id == user.id,
                    MovieEvaluation.persona_id.is_(None),
                )
                .all()
            )
        return {row.movie_id for row in rows}

    def _youtube_trailer_load(self):
        return selectinload(Movie.youtube_videos.and_(YoutubeVideo.is_trailer.is_(True)))

    def _movie_load_options(self):
        return [
            selectinload(Movie.titles),
            self._youtube_trailer_load(),
        ]

    def _has_trailer_filter(self, query):
        return query.filter(
            Movie.youtube_videos.any(YoutubeVideo.is_trailer.is_(True))
        )

    def _fetch_movies_by_ids(
        self,
        db: Session,
        movie_ids: list[UUID],
        exclude_ids: Set[UUID],
    ) -> list[Movie]:
        if not movie_ids:
            return []

        filtered_ids = [mid for mid in movie_ids if mid not in exclude_ids]
        if not filtered_ids:
            return []

        query = movie_read_service.base_query(db).filter(Movie.id.in_(filtered_ids))
        query = self._has_trailer_filter(query)
        movies = query.options(*self._movie_load_options()).all()
        movies_by_id = {movie.id: movie for movie in movies}

        return [movies_by_id[mid] for mid in filtered_ids if mid in movies_by_id]

    def _fetch_trailer_movies_from_db(
        self,
        db: Session,
        exclude_ids: Set[UUID],
        limit: int,
    ) -> list[Movie]:
        query = movie_read_service.base_query(db)
        query = self._has_trailer_filter(query)
        if exclude_ids:
            query = query.filter(~Movie.id.in_(exclude_ids))
        return (
            query.options(*self._movie_load_options())
            .order_by(Movie.id.desc())
            .limit(limit)
            .all()
        )

    async def get_movies_to_evaluate(
        self,
        db: Session,
        user: User,
        persona_id: Optional[UUID] = None,
        limit: int = 20,
    ) -> MovieToEvaluateListResponse:
        if persona_id:
            self._verify_persona_ownership(db, persona_id, user)

        evaluated_ids = self._get_evaluated_movie_ids(db, user, persona_id)
        collected: list[Movie] = []
        collected_ids: Set[UUID] = set()

        if persona_id:
            ml_response = await safe_ml_call(
                "recommend movie for evaluation",
                lambda: movie_recommendation_service.recommend(
                    user_id=user.id,
                    persona_id=persona_id,
                    query="예고편 평가 추천",
                ),
            )
            if ml_response:
                recommended_ids: list[UUID] = []
                for item in ml_response.movies:
                    try:
                        recommended_ids.append(UUID(item.movie_id))
                    except ValueError:
                        continue

                ml_movies = self._fetch_movies_by_ids(db, recommended_ids, evaluated_ids)
                for movie in ml_movies:
                    if movie.id not in collected_ids:
                        collected.append(movie)
                        collected_ids.add(movie.id)
                        if len(collected) >= limit:
                            break

        if len(collected) < limit:
            remaining = limit - len(collected)
            exclude = evaluated_ids | collected_ids
            db_movies = self._fetch_trailer_movies_from_db(db, exclude, remaining)
            for movie in db_movies:
                collected.append(movie)
                collected_ids.add(movie.id)

        return MovieToEvaluateListResponse(
            items=[MovieMapper.to_movie_with_trailers(movie) for movie in collected]
        )

    async def evaluate_movie(
        self,
        db: Session,
        user: User,
        movie_id: UUID,
        evaluation: Literal["LIKE", "DISLIKE"],
        persona_id: Optional[UUID] = None,
    ) -> MovieEvaluationResponse:
        if persona_id:
            self._verify_persona_ownership(db, persona_id, user)

        movie = (
            movie_read_service.base_query(db)
            .filter(Movie.id == movie_id)
            .options(*self._movie_load_options())
            .first()
        )
        if not movie or not any(v.is_trailer for v in (movie.youtube_videos or [])):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=_error_detail(ERROR_MOVIE_NOT_FOUND),
            )

        duplicate_query = db.query(MovieEvaluation).filter(
            MovieEvaluation.movie_id == movie_id
        )
        if persona_id:
            duplicate_query = duplicate_query.filter(MovieEvaluation.persona_id == persona_id)
        else:
            duplicate_query = duplicate_query.filter(
                MovieEvaluation.user_id == user.id,
                MovieEvaluation.persona_id.is_(None),
            )

        if duplicate_query.first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=_error_detail(ERROR_ALREADY_EVALUATED),
            )

        new_evaluation = MovieEvaluation(
            user_id=user.id,
            persona_id=persona_id,
            movie_id=movie_id,
            evaluation=evaluation,
        )
        db.add(new_evaluation)
        db.commit()
        db.refresh(new_evaluation)

        await movie_evaluation_ml_sync_service.sync_movie_judge(
            movie_id=movie_id,
            user_id=user.id,
            persona_id=persona_id,
            evaluation=evaluation,
            created_at=new_evaluation.created_at,
        )

        return MovieEvaluationResponse(
            message="Movie evaluation recorded successfully.",
            user_id=user.id,
            persona_id=persona_id,
            movie_id=movie_id,
            evaluation=evaluation,
        )

    def list_evaluations(
        self,
        db: Session,
        user: User,
        persona_id: Optional[UUID] = None,
        cursor: Optional[int] = None,
        limit: int = 20,
    ) -> MovieEvaluationListResponse:
        if persona_id:
            self._verify_persona_ownership(db, persona_id, user)

        query = (
            db.query(MovieEvaluation)
            .filter(MovieEvaluation.user_id == user.id)
            .options(
                selectinload(MovieEvaluation.persona),
                selectinload(MovieEvaluation.movie).selectinload(Movie.titles),
                selectinload(MovieEvaluation.movie).selectinload(
                    Movie.youtube_videos.and_(YoutubeVideo.is_trailer.is_(True))
                ),
            )
        )

        if persona_id:
            query = query.filter(MovieEvaluation.persona_id == persona_id)

        if cursor:
            query = query.filter(MovieEvaluation.id < cursor)

        evaluations = query.order_by(MovieEvaluation.id.desc()).limit(limit).all()

        items = [
            MovieEvaluationItem(
                id=eval_rec.id,
                evaluation=eval_rec.evaluation,
                created_at=eval_rec.created_at,
                persona=PersonaMapper.to_persona(eval_rec.persona) if eval_rec.persona else None,
                movie=MovieMapper.to_movie_with_trailers(eval_rec.movie),
            )
            for eval_rec in evaluations
        ]

        has_next = len(evaluations) == limit
        next_cursor = evaluations[-1].id if has_next else None

        return MovieEvaluationListResponse(
            items=items,
            next_cursor=next_cursor,
            has_next=has_next,
        )


movie_evaluation_service = MovieEvaluationService()
