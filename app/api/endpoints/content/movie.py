import httpx
from fastapi import APIRouter, Depends, HTTPException
from uuid import UUID
from app.core.config import settings
from app.api.deps import get_current_persona, get_active_user
from app.models.user import User
from app.schemas.response.movie import WatchMovieResponse, MovieRecommendationResponse
from app.schemas.errors import ERROR_ML_SERVER_UNAVAILABLE

router = APIRouter()

@router.post("/{movie_id}/watch", response_model=WatchMovieResponse)
async def watch_movie(movie_id: int, current_user: User = Depends(get_active_user)):
    # 이 엔드포인트는 프론트엔드의 /api/logs/activity 호출로 대체될 수 있습니다.
    # 현재는 아무 동작도 하지 않습니다.
    return {"status": "success", "message": f"User {current_user.id} watched movie {movie_id}"}

@router.get(
    "/recommend",
    response_model=MovieRecommendationResponse,
    responses={503: ERROR_ML_SERVER_UNAVAILABLE}
)
async def get_movies(active_persona_id: UUID = Depends(get_current_persona)):
    """
    [API Gateway] 프론트엔드의 영화 추천 요청을 받아 ML 서버로 전달하고,
    계산된 맞춤 추천 영화 목록을 그대로 프론트엔드에 반환합니다.
    """
    ML_API_URL = f"{settings.ML_API_BASE_URL}/api/recommendation/movies?persona_id={active_persona_id}"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(ML_API_URL, timeout=3.0)
            response.raise_for_status()
            
            # ML 서버가 반환한 JSON(추천 영화 목록)을 프론트엔드에 그대로 전달
            return response.json()
            
    except httpx.RequestError:
        # 추천 서버가 다운되었거나 타임아웃 발생 시 503 에러 반환 (또는 Fallback 로직 추가 가능)
        raise HTTPException(status_code=503, detail={"code": "ML_SERVER_UNAVAILABLE", "message": "추천 서버(ML/VLLM)와 통신할 수 없거나 응답이 지연되고 있습니다."})
