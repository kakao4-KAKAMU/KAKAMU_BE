from fastapi import APIRouter
from uuid import UUID
from app.service.recommendation import recommendation_service

router = APIRouter()

@router.post("/activity")
async def test_record_activity(movie_id: int, genres: str, persona_id: UUID):
    """페르소나 활동 기록 테스트 (genres는 'Action,Sci-Fi' 형태)"""
    genre_list = [g.strip() for g in genres.split(",")]
    await recommendation_service.record_activity(persona_id, movie_id, "view")
    await recommendation_service.update_persona_preference(persona_id, genre_list)
    return {"message": "활동 기록 완료"}

@router.get("/context/{persona_id}")
async def test_get_context(persona_id: UUID):
    """페르소나의 실시간 컨텍스트 조회 테스트"""
    context = await recommendation_service.get_persona_context(persona_id)
    return context
