import httpx
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from uuid import UUID
from app.core.config import settings
from app.api.deps import get_current_persona
from app.schemas.errors import ERROR_ML_SERVER_UNAVAILABLE
from app.schemas.request.chat import ChatRequest

router = APIRouter()

# 스트리밍 방식에서는 response_model을 사용하지 않고 StreamingResponse를 직접 반환합니다.
@router.post("/completions", responses={503: ERROR_ML_SERVER_UNAVAILABLE})
async def chat_with_vllm(
    req: ChatRequest,
    active_persona_id: UUID = Depends(get_current_persona)
):
    """
    [API Gateway] 프론트엔드의 채팅 메시지를 VLLM 서버로 전달하여 챗봇 응답을 스트리밍(SSE)으로 반환합니다.
    """
    # VLLM 서버의 OpenAI 호환 completions API 경로 (실제 VLLM 설정에 따라 다를 수 있음)
    VLLM_API_URL = f"{settings.VLLM_GENBASE_URL}/chat/completions"
    
    # 이전 대화 내역이 있다면 가져오고, 마지막에 현재 사용자의 메시지를 추가합니다.
    messages = req.history.copy() if req.history else []
    messages.append({"role": "user", "content": req.message})

    payload = {
        "model": "your-model-name", # 실제 서빙 중인 LLM 모델명 입력
        "messages": messages,
        "stream": True # VLLM 서버에 실시간 스트리밍 응답을 요청합니다.
    }

    async def event_generator():
        try:
            async with httpx.AsyncClient() as client:
                # 챗봇 텍스트 생성은 시간이 걸릴 수 있으므로 timeout을 넉넉히(예: 60초) 설정합니다.
                async with client.stream("POST", VLLM_API_URL, json=payload, timeout=60.0) as response:
                    response.raise_for_status()
                    # VLLM이 보내는 데이터 조각(Chunk)을 받는 즉시 프론트엔드로 토스합니다.
                    async for chunk in response.aiter_bytes():
                        yield chunk
        except httpx.RequestError:
            # 에러 발생 시 SSE 규격(data: ...)에 맞춰 에러 메시지를 보냅니다.
            yield b'data: {"error": "ML_SERVER_UNAVAILABLE"}\n\n'

    # 미디어 타입을 text/event-stream으로 지정하여 SSE 연결을 성립시킵니다.
    return StreamingResponse(event_generator(), media_type="text/event-stream")