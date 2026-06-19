from fastapi import APIRouter, HTTPException, status
from typing import List

from app.service.movie.dummy import DUMMY_MOVIES
from app.models.in_memory import persona_evaluations
from app.schemas.request.movie_analyzer import MovieEvaluationRequest
from app.schemas.response.movie_analyzer import MovieEvaluationResponse

router = APIRouter()

@router.get("/movies", response_model=List[dict], summary="평가할 영화 목록 조회")
async def get_movies_to_evaluate():
    """
    사용자가 평가할 수 있는 영화 목록(ID, 제목, 예고편 URL)을 반환합니다.
    """
    return DUMMY_MOVIES

@router.post("/movies/evaluate", response_model=MovieEvaluationResponse, summary="영화 예고편 평가 기록")
async def evaluate_movie_trailer(request: MovieEvaluationRequest):
    """
    특정 페르소나가 영화 예고편을 'LIKE' 또는 'DISLIKE'로 평가한 기록을 저장합니다.
    """
    persona_id = request.persona_id
    movie_id = request.movie_id
    evaluation = request.evaluation

    if movie_id not in [movie["movie_id"] for movie in DUMMY_MOVIES]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Movie with ID '{movie_id}' not found."
        )

    if persona_id not in persona_evaluations:
        persona_evaluations[persona_id] = {}
    
    persona_evaluations[persona_id][movie_id] = evaluation

    return MovieEvaluationResponse(
        message="Movie evaluation recorded successfully.",
        persona_id=persona_id,
        movie_id=movie_id,
        evaluation=evaluation
    )

@router.get("/persona/{persona_id}/evaluations", response_model=dict, summary="페르소나별 영화 평가 기록 조회")
async def get_persona_evaluations(persona_id: str):
    """
    특정 페르소나의 영화 평가 기록을 조회합니다.
    """
    if persona_id not in persona_evaluations:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No evaluations found for persona ID '{persona_id}'."
        )
    return persona_evaluations[persona_id]
