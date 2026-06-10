import httpx
from fastapi import APIRouter, Depends, HTTPException
from uuid import UUID
from app.core.config import settings
from app.api.deps import get_current_persona
from app.schemas.errors import ERROR_ML_SERVER_UNAVAILABLE
from app.schemas.request.chat import ChatRequest
from app.schemas.response.chat import ChatCompletionResponse

router = APIRouter()

@router.post("/completions", response_model=ChatCompletionResponse, responses={503: ERROR_ML_SERVER_UNAVAILABLE})
async def chat_with_vllm(
    req: ChatRequest,
    active_persona_id: UUID = Depends(get_current_persona)
):
    """
    [API Gateway] 프론트엔드의 채팅 메시지를 VLLM 서버로 전달하여 챗봇 응답을 반환합니다.
    """
    # VLLM 서버의 OpenAI 호환 completions API 경로 (실제 VLLM 설정에 따라 다를 수 있음)
    VLLM_API_URL = f"{settings.VLLM_GENBASE_URL}/chat/completions"
    
    payload = {
        "model": "your-model-name", # 실제 서빙 중인 LLM 모델명 입력
        "messages": [{"role": "user", "content": req.message}]
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(VLLM_API_URL, json=payload, timeout=10.0)
            response.raise_for_status()
            return {"status": "success", "data": response.json()}
            
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail={"code": "ML_SERVER_UNAVAILABLE", "message": "챗봇 서버와 통신할 수 없습니다."})