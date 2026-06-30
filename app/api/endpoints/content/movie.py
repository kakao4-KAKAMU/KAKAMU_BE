from fastapi import APIRouter, Depends, HTTPException, Query
from uuid import UUID
import httpx
from sqlalchemy.orm import Session

from app.api.deps import get_current_persona, get_active_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.response.movie import MovieDetailResponse, WatchMovieResponse
from app.schemas.response.ml.recommend import MlMovieRecommendResponse
from app.schemas.errors import ERROR_ML_SERVER_UNAVAILABLE, ERROR_MOVIE_NOT_FOUND
from app.service.movie.get_movie import movie_read_service
from app.service.movie.recommendation import movie_recommendation_service

router = APIRouter()


@router.get(
    "/{movie_id}",
    response_model=MovieDetailResponse,
    responses={404: ERROR_MOVIE_NOT_FOUND},
    summary="영화 상세 조회",
)
def get_movie_detail(movie_id: UUID, db: Session = Depends(get_db)):
    return movie_read_service.get_movie_detail(db, movie_id)


@router.post(
    "/{movie_id}/watch",
    response_model=WatchMovieResponse,
    summary="영화 시청 기록 추가"
)
async def watch_movie(movie_id: UUID, current_user: User = Depends(get_active_user)):
    return {"status": "success", "message": f"User {current_user.id} watched movie {movie_id}"}

@router.get(
    "/recommend",
    response_model=MlMovieRecommendResponse,
    responses={503: ERROR_ML_SERVER_UNAVAILABLE},
    summary="맞춤 영화 추천"
)
async def get_movies(
    query: str = Query(default="맞춤 영화 추천", min_length=1, description="추천 쿼리"),
    current_user: User = Depends(get_active_user),
    active_persona_id: UUID = Depends(get_current_persona),
):
    try:
        return await movie_recommendation_service.recommend(
            user_id=current_user.id,
            persona_id=active_persona_id,
            query=query,
        )
    except httpx.RequestError:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "ML_SERVER_UNAVAILABLE",
                "message": "추천 서버(ML/VLLM)와 통신할 수 없거나 응답이 지연되고 있습니다.",
            },
        )
