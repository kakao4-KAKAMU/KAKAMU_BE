from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.service.recommendation import recommendation_service
from app.service.persona import PersonaService
from app.api.deps import get_current_persona

router = APIRouter()

@router.post("/{movie_id}/watch")
async def watch_movie(movie_id: int, user_id: int, db: Session = Depends(get_db)):
    persona_service = PersonaService()
    # 1. 현재 어떤 페르소나로 접속 중인지 Redis에서 조회
    persona_id = await persona_service.get_current_active_persona_id(db, user_id)
    if not persona_id:
        return {"error": "페르소나를 먼저 선택하세요."}

    # 2. 활동 기록 및 취향 반영 (장르는 DB에서 가져왔다고 가정)
    await recommendation_service.record_activity(persona_id, movie_id, "view")
    await recommendation_service.update_persona_preference(persona_id, ["Action", "Sci-Fi"])
    
    return {"message": f"Persona {persona_id} watched movie {movie_id}"}

@router.get("/recommend")
async def get_movies(active_persona_id: int = Depends(get_current_persona)):
    # 1. 이제 active_persona_id를 바로 사용 가능!
    # 2. 이 ID로 RecommendationService의 context를 불러옴
    context = await recommendation_service.get_recent_persona_context(active_persona_id)
    return {"recommendations": "...", "for_persona": active_persona_id}
