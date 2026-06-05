from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from uuid import UUID
from app.db.session import get_db
from app.service.recommendation.recommendation_service import recommendation_service
from app.api.deps import get_current_persona

router = APIRouter()

@router.post("/{movie_id}/watch")
async def watch_movie(movie_id: int, persona_id: UUID = Depends(get_current_persona)):
    # 이 엔드포인트는 프론트엔드의 /api/logs/activity 호출로 대체될 수 있습니다.
    # 현재는 아무 동작도 하지 않습니다.
    return {"message": f"Persona {persona_id} watched movie {movie_id}"}

@router.get("/recommend")
async def get_movies(active_persona_id: UUID = Depends(get_current_persona)):
    # ML 서버 연동 후 추천 결과를 서빙할 예정입니다.
    return {"recommendations": "추천 데이터 연동 준비 중", "for_persona": active_persona_id}
