from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime

from app.db.session import get_db
from app.models import Persona, User, MovieEvaluation
from app.api.deps.auth import get_active_user
from app.service.movie.dummy import DUMMY_MOVIES
from app.schemas.request.movie_analyzer import MovieEvaluationRequest
from app.schemas.response.movie_analyzer import MovieEvaluationResponse

from app.models.ml import JudgeType
from app.schemas.request.ml.ingest import MlIngestMovieJudgeEnvelope, MlIngestMovieJudgePayload
from app.service.ml import ml_ingest_service
from app.service.ml.sync import safe_ml_call

from app.schemas.errors import (
    ERROR_PERSONA_NOT_FOUND_OR_FORBIDDEN,
    ERROR_ALREADY_EVALUATED,
    ERROR_MOVIE_NOT_FOUND
)

router = APIRouter()

# 중복 검색 연산을 피하기 위한 더미 영화 ID 집합 정의
DUMMY_MOVIE_IDS = {movie["movie_id"] for movie in DUMMY_MOVIES}

def verify_persona_ownership(persona_id: str, current_user: User, db: Session) -> Persona:
    try:
        persona_uuid = UUID(persona_id)
        persona = db.get(Persona, persona_uuid)
    except ValueError:
        persona = None

    if not persona or persona.user_id != current_user.id or persona.status == "DELETED":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=ERROR_PERSONA_NOT_FOUND_OR_FORBIDDEN["content"]["application/json"]["example"]["detail"]
        )
    return persona

@router.get(
    "/movies",
    response_model=List[dict],
    responses={
        403: ERROR_PERSONA_NOT_FOUND_OR_FORBIDDEN
    },
    summary="평가할 영화 목록 조회"
)
async def get_movies_to_evaluate(
    persona_id: str,
    current_user: User = Depends(get_active_user),
    db: Session = Depends(get_db)
):
    """
    로그인한 회원의 페르소나가 평가할 수 있는 영화 목록(ID, 제목, 예고편 URL) 중,
    아직 평가하지 않은 영화 목록만 반환합니다.
    """
    # 페르소나 소유권 검증
    verify_persona_ownership(persona_id, current_user, db)

    # DB에서 이미 평가 완료한 영화 ID 목록 조회
    persona_uuid = UUID(persona_id)
    evaluated_records = db.query(MovieEvaluation.movie_id).filter(
        MovieEvaluation.persona_id == persona_uuid
    ).all()
    evaluated_ids = {record.movie_id for record in evaluated_records}

    # 평가되지 않은 영화만 필터링
    unrated_movies = [
        movie for movie in DUMMY_MOVIES if movie["movie_id"] not in evaluated_ids
    ]
    return unrated_movies

@router.post(
    "/movies/evaluate",
    response_model=MovieEvaluationResponse,
    responses={
        400: ERROR_ALREADY_EVALUATED,
        403: ERROR_PERSONA_NOT_FOUND_OR_FORBIDDEN,
        404: ERROR_MOVIE_NOT_FOUND
    },
    summary="영화 예고편 평가 기록"
)
async def evaluate_movie_trailer(
    request: MovieEvaluationRequest,
    current_user: User = Depends(get_active_user),
    db: Session = Depends(get_db)
):
    """
    로그인한 회원의 특정 페르소나가 영화 예고편을 'LIKE' 또는 'DISLIKE'로 평가한 기록을 저장하고,
    그 반응을 추천 시스템(ML Ingest API)에 전달합니다.
    """
    persona_id = request.persona_id
    movie_id = request.movie_id
    evaluation = request.evaluation

    if movie_id not in DUMMY_MOVIE_IDS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ERROR_MOVIE_NOT_FOUND["content"]["application/json"]["example"]["detail"]
        )

    # 페르소나 소유권 검증 (DB)
    persona = verify_persona_ownership(persona_id, current_user, db)

    # DB에서 중복 평가 여부 검증
    persona_uuid = UUID(persona_id)
    existing_eval = db.query(MovieEvaluation).filter(
        MovieEvaluation.persona_id == persona_uuid,
        MovieEvaluation.movie_id == movie_id
    ).first()

    if existing_eval:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_ALREADY_EVALUATED["content"]["application/json"]["example"]["detail"]
        )

    # DB에 평가 정보 기록
    new_evaluation = MovieEvaluation(
        persona_id=persona_uuid,
        movie_id=movie_id,
        evaluation=evaluation
    )
    db.add(new_evaluation)
    db.commit()

    # 추천 시스템(ML API)으로 활동 로그 전송
    judge_type = JudgeType.LIKE if evaluation == "LIKE" else JudgeType.DISLIKE
    envelope = MlIngestMovieJudgeEnvelope(
        payload=MlIngestMovieJudgePayload(
            movie_id=movie_id,
            user_id=str(persona.user_id),
            persona_id=persona_id,
            judge_type=judge_type,
            created_at=datetime.utcnow()
        )
    )
    
    # safe_ml_call을 활용하여 API 호출 에러에 대응
    await safe_ml_call(
        "ingest movie judge",
        lambda: ml_ingest_service.judge_movie(envelope)
    )

    return MovieEvaluationResponse(
        message="Movie evaluation recorded successfully.",
        persona_id=persona_id,
        movie_id=movie_id,
        evaluation=evaluation
    )

@router.get(
    "/persona/{persona_id}/evaluations",
    response_model=dict,
    responses={
        403: ERROR_PERSONA_NOT_FOUND_OR_FORBIDDEN
    },
    summary="페르소나별 영화 평가 기록 조회"
)
async def get_persona_evaluations(
    persona_id: str,
    current_user: User = Depends(get_active_user),
    db: Session = Depends(get_db)
):
    """
    로그인한 회원의 특정 페르소나의 영화 평가 기록을 조회합니다.
    """
    # 페르소나 소유권 검증
    verify_persona_ownership(persona_id, current_user, db)

    persona_uuid = UUID(persona_id)
    evaluations = db.query(MovieEvaluation).filter(
        MovieEvaluation.persona_id == persona_uuid
    ).all()

    if not evaluations:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No evaluations found for persona ID '{persona_id}'."
        )
    
    # 딕셔너리 형태로 변환: {"movie_id": "LIKE"/"DISLIKE"}
    return {eval_rec.movie_id: eval_rec.evaluation for eval_rec in evaluations}
