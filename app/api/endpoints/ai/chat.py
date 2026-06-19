from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from uuid import UUID

from app.db.session import get_db
from app.api.deps import get_current_persona
from app.schemas.request.chat import ChatRequest
from app.schemas.response.chat import ChatCompletionResponse
from app.service.ai.chat_service import chat_service

router = APIRouter()

@router.post(
    "/completions",
    response_model=ChatCompletionResponse,
    summary="VLLM 기반 AI 챗봇 대화 생성"
)
async def chat_completions(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_persona_id: UUID = Depends(get_current_persona)
):
    """이전 대화 내역(Session)과 현재 페르소나 정보를 결합하여 챗봇 응답을 생성합니다."""
    response_data = await chat_service.generate_chat_response(db, current_persona_id, request)
    
    return ChatCompletionResponse(
        session_id=request.session_id,
        data=response_data
    )