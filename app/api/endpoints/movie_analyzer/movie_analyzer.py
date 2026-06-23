from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps.auth import get_active_user
from app.db.session import get_db
from app.models import User
from app.schemas.errors import (
    ERROR_ALREADY_EVALUATED,
    ERROR_MOVIE_NOT_FOUND,
    ERROR_PERSONA_NOT_FOUND_OR_FORBIDDEN,
)
from app.schemas.request.movie_analyzer import MovieEvaluationRequest
from app.schemas.response.movie_analyzer import (
    MovieEvaluationListResponse,
    MovieEvaluationResponse,
    MovieToEvaluateListResponse,
)
from app.service.movie.evaluation_service import movie_evaluation_service

router = APIRouter()


@router.get(
    "/movies",
    response_model=MovieToEvaluateListResponse,
    responses={
        403: ERROR_PERSONA_NOT_FOUND_OR_FORBIDDEN,
    },
    summary="평가할 영화 목록 조회",
)
async def get_movies_to_evaluate(
    persona_id: Optional[UUID] = None,
    limit: int = Query(default=20, ge=1, le=50),
    current_user: User = Depends(get_active_user),
    db: Session = Depends(get_db),
):
    """
    로그인한 회원이 평가할 수 있는 영화 목록을 반환합니다.
    ML 추천 영화를 우선 제공하고, 부족한 경우 DB 트레일러 영화로 보충합니다.
    """
    return await movie_evaluation_service.get_movies_to_evaluate(
        db,
        current_user,
        persona_id=persona_id,
        limit=limit,
    )


@router.post(
    "/movies/evaluate",
    response_model=MovieEvaluationResponse,
    responses={
        400: ERROR_ALREADY_EVALUATED,
        403: ERROR_PERSONA_NOT_FOUND_OR_FORBIDDEN,
        404: ERROR_MOVIE_NOT_FOUND,
    },
    summary="영화 예고편 평가 기록",
)
async def evaluate_movie_trailer(
    request: MovieEvaluationRequest,
    current_user: User = Depends(get_active_user),
    db: Session = Depends(get_db),
):
    """
    로그인한 회원이 영화 예고편을 'LIKE' 또는 'DISLIKE'로 평가한 기록을 저장하고,
    그 반응을 추천 시스템(ML Ingest API)에 전달합니다.
    """
    return await movie_evaluation_service.evaluate_movie(
        db,
        current_user,
        movie_id=request.movie_id,
        evaluation=request.evaluation,
        persona_id=request.persona_id,
    )


@router.get(
    "/evaluations",
    response_model=MovieEvaluationListResponse,
    responses={
        403: ERROR_PERSONA_NOT_FOUND_OR_FORBIDDEN,
    },
    summary="영화 평가 기록 조회",
)
async def list_movie_evaluations(
    persona_id: Optional[UUID] = None,
    cursor: Optional[int] = None,
    limit: int = Query(default=20, ge=1, le=50),
    current_user: User = Depends(get_active_user),
    db: Session = Depends(get_db),
):
    """
    로그인한 회원의 영화 평가 기록을 커서 페이지네이션으로 조회합니다.
    persona_id를 지정하면 해당 페르소나의 평가만 필터링합니다.
    """
    return movie_evaluation_service.list_evaluations(
        db,
        current_user,
        persona_id=persona_id,
        cursor=cursor,
        limit=limit,
    )
