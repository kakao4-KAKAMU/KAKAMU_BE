import json
import httpx
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from uuid import UUID

from app.db.session import get_db
from app.api.deps import get_current_persona, get_active_user
from app.models import User
from app.schemas.errors import ERROR_ML_SERVER_UNAVAILABLE
from app.schemas.request.chat import ChatRequest
from app.service.ai.chat_service import chat_service
from app.core.config import settings

# OpenTelemetry trace 임포트
from opentelemetry import trace

router = APIRouter()
tracer = trace.get_tracer(__name__)

@router.post(
    "/completions",
    responses={503: ERROR_ML_SERVER_UNAVAILABLE},
    summary="VLLM 기반 AI 챗봇 대화 생성 (스트리밍 SSE)"
)
async def chat_completions(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_active_user),
    current_persona_id: UUID = Depends(get_current_persona)
):
    """
    이전 대화 내역(Redis)과 페르소나 취향을 결합하여 VLLM 서버로 전달한 후, 
    생성된 챗봇 답변을 SSE 스트리밍(text/event-stream)으로 클라이언트에 전달하며 
    동시에 대화 이력을 Redis에 안전하게 캐싱 저장합니다.
    """
    # 1. 서비스단을 통한 페이로드 조립 및 Redis key 획득
    payload_messages, redis_key = await chat_service.prepare_chat_messages(
        db, current_persona_id, request.session_id, request.message
    )

    # 2. VLLM 서버 completions 스트리밍 API 경로 및 페이로드 구성
    vllm_api_url = f"{settings.ML_API_BASE_URL}/v1/chat/completions"
    
    payload = {
        "model": "vllm-model",
        "messages": payload_messages,
        "max_tokens": 1024,
        "temperature": 0.7,
        "stream": True
    }

    async def event_generator():
        # OpenTelemetry Span으로 묶어 추적
        with tracer.start_as_current_span("vllm_chat_stream_request") as span:
            span.set_attribute("user.id", str(current_user.id))
            span.set_attribute("persona.id", str(current_persona_id))
            span.set_attribute("session.id", request.session_id)
            span.set_attribute("vllm.url", vllm_api_url)

            # 완성된 챗봇 답변 텍스트를 누적하기 위한 버퍼
            assistant_content_accumulated = []

            try:
                # ML API 주소가 정의되지 않은 경우의 Fallback Mock 데이터 스트리밍 지원
                if not settings.ML_API_BASE_URL:
                    fallback_text = f"'{request.message}'에 대한 답변입니다. (현재 백엔드에 ML_API_BASE_URL 환경변수가 설정되지 않아 Mock 데이터를 반환합니다.)"
                    span.add_event("vllm_fallback_triggered")
                    
                    # OpenAI 호환 SSE chunk 포맷으로 조각내어 스트리밍 전송
                    words = fallback_text.split(" ")
                    for word in words:
                        chunk_data = {
                            "choices": [{
                                "delta": {"content": word + " "}
                            }]
                        }
                        yield f"data: {json.dumps(chunk_data)}\n\n".encode("utf-8")
                        assistant_content_accumulated.append(word + " ")
                    yield b"data: [DONE]\n\n"
                    
                    # 대화 히스토리 저장
                    # system 프롬프트를 제외한 사용자 메시지가 포함된 history_messages를 구합니다.
                    history_messages = payload_messages[1:] # system 프롬프트 제외
                    await chat_service.save_chat_history(
                        redis_key, 
                        history_messages, 
                        "".join(assistant_content_accumulated)
                    )
                    span.set_status(trace.StatusCode.OK)
                    return

                # 실제 VLLM 서버로 통신
                async with httpx.AsyncClient() as client:
                    async with client.stream("POST", vllm_api_url, json=payload, timeout=60.0) as response:
                        response.raise_for_status()
                        span.add_event("vllm_connection_established")

                        async for chunk in response.aiter_lines():
                            if not chunk:
                                continue
                            
                            # 클라이언트에 그대로 chunk 전달
                            yield (chunk + "\n\n").encode("utf-8")

                            # 청크에서 텍스트 정보 파싱하여 완성형 문자열 빌드
                            if chunk.startswith("data: ") and not chunk.endswith("[DONE]"):
                                try:
                                    chunk_json = json.loads(chunk[6:])
                                    delta = chunk_json.get("choices", [{}])[0].get("delta", {})
                                    content = delta.get("content", "")
                                    if content:
                                        assistant_content_accumulated.append(content)
                                except Exception:
                                    pass

                        span.add_event("vllm_stream_completed")
                        span.set_status(trace.StatusCode.OK)

                # 스트리밍이 정상 완료되면 누적된 챗봇 답변을 대화 세션 기록에 캐싱
                assistant_response = "".join(assistant_content_accumulated)
                history_messages = payload_messages[1:] # system 프롬프트 제외
                await chat_service.save_chat_history(redis_key, history_messages, assistant_response)

            except httpx.RequestError as e:
                span.record_exception(e)
                span.set_status(trace.StatusCode.ERROR, description="VLLM Server Request Error")
                yield b'data: {"error": "ML_SERVER_UNAVAILABLE"}\n\n'

            except Exception as e:
                span.record_exception(e)
                span.set_status(trace.StatusCode.ERROR, description=str(e))
                raise

    return StreamingResponse(event_generator(), media_type="text/event-stream")
