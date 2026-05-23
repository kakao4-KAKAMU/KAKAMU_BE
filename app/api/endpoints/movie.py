from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from uuid import UUID
from app.db.session import get_db
from app.service.recommendation import recommendation_service
from app.api.deps import get_current_persona

router = APIRouter()

@router.post("/{movie_id}/watch")
async def watch_movie(movie_id: int, persona_id: UUID = Depends(get_current_persona)):
    # 1. JWT 토큰에서 바로 추출된 페르소나로 활동 기록 및 취향 반영
    await recommendation_service.record_activity(persona_id, movie_id, "view")
    await recommendation_service.update_persona_preference(persona_id, ["Action", "Sci-Fi"])
    
    return {"message": f"Persona {persona_id} watched movie {movie_id}"}

@router.get("/recommend")
async def get_movies(active_persona_id: UUID = Depends(get_current_persona)):
    # 1. 이제 active_persona_id를 바로 사용 가능!
    # 2. 이 ID로 RecommendationService의 context를 불러옴
    context = await recommendation_service.get_recent_persona_context(active_persona_id)
    return {"recommendations": "...", "for_persona": active_persona_id}
