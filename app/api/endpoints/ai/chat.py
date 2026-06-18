import httpx
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from uuid import UUID
from app.core.config import settings
from app.api.deps import get_current_persona, get_active_user
from app.models import User
from app.schemas.errors import ERROR_ML_SERVER_UNAVAILABLE
from app.schemas.request.chat import ChatRequest

# [추가] OpenTelemetry trace 임포트
from opentelemetry import trace

router = APIRouter()

# [추가] 현재 모듈(chat.py)에 대한 tracer 인스턴스 획득
tracer = trace.get_tracer(__name__)


# 스트리밍 방식에서는 response_model을 사용하지 않고 StreamingResponse를 직접 반환합니다.
@router.post(
    "/completions",
    responses={503: ERROR_ML_SERVER_UNAVAILABLE},
    summary="챗봇 텍스트 스트리밍 생성"
)
async def chat_with_vllm(
        req: ChatRequest,
        current_user: User = Depends(get_active_user),
        active_persona_id: UUID = Depends(get_current_persona)
):
    """
    [API Gateway] 프론트엔드의 채팅 메시지를 VLLM 서버로 전달하여 챗봇 응답을 스트리밍(SSE)으로 반환합니다.
    """
    # 확인된 VLLM 서버의 노드 단위 SSE 스트리밍 API 경로
    VLLM_API_URL = f"{settings.VLLM_GENBASE_URL}/chat/stream"

    # Swagger에서 확인한 Request Body 스키마에 맞춰 페이로드 재구성
    payload = {
        "user_id": str(current_user.id),  # 실제 로그인한 유저 본인의 ID 전달
        "session_id": req.session_id,  # 프론트엔드에서 전달받은 세션 ID를 그대로 넘김
        "message": req.message,
        "top_k": 10,
        "max_toxicity": 0.7
    }

    async def event_generator():
        # [추가] 외부 VLLM 서버 통신 구간을 하나의 Span으로 묶어서 추적
        with tracer.start_as_current_span("vllm_chat_stream_request") as span:

            # [추가] Grafana Tempo 등에서 필터링하기 쉽도록 사용자 및 요청 메타데이터 기록
            span.set_attribute("user.id", str(current_user.id))
            span.set_attribute("session.id", req.session_id)
            span.set_attribute("vllm.url", VLLM_API_URL)

            try:
                async with httpx.AsyncClient() as client:
                    # 챗봇 텍스트 생성은 시간이 걸릴 수 있으므로 timeout을 넉넉히(예: 60초) 설정합니다.
                    async with client.stream("POST", VLLM_API_URL, json=payload, timeout=60.0) as response:
                        response.raise_for_status()

                        # [추가] VLLM 서버 연결 성공 (TTFT - 첫 토큰이 나오기까지의 시간 측정을 위한 이벤트 기록)
                        span.add_event("vllm_connection_established")

                        # VLLM이 보내는 데이터 조각(Chunk)을 받는 즉시 프론트엔드로 토스합니다.
                        async for chunk in response.aiter_bytes():
                            yield chunk

                        # [추가] 정상적으로 전체 스트리밍 응답이 끝난 시점 기록
                        span.add_event("vllm_stream_completed")
                        span.set_status(trace.StatusCode.OK)

            except httpx.RequestError as e:
                # [추가] VLLM 서버 접속 에러 혹은 타임아웃 발생 시 예외(Exception)와 에러 상태 기록
                span.record_exception(e)
                span.set_status(trace.StatusCode.ERROR, description="VLLM Server Request Error")
                # 에러 발생 시 SSE 규격(data: ...)에 맞춰 에러 메시지를 보냅니다.
                yield b'data: {"error": "ML_SERVER_UNAVAILABLE"}\n\n'

            except Exception as e:
                # [추가] 그 외 예기치 못한 에러 발생 시 기록
                span.record_exception(e)
                span.set_status(trace.StatusCode.ERROR, description=str(e))
                raise

    # 미디어 타입을 text/event-stream으로 지정하여 SSE 연결을 성립시킵니다.
    return StreamingResponse(event_generator(), media_type="text/event-stream")