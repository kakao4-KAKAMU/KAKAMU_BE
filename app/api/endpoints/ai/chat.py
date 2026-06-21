import httpx
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from uuid import UUID
from app.api.deps import get_current_persona, get_active_user
from app.models import User
from app.schemas.errors import ERROR_ML_SERVER_UNAVAILABLE
from app.schemas.request.chat import ChatRequest
from app.schemas.request.ml.chat import MlChatStreamRequest
from app.service.ml import ml_chat_service

from opentelemetry import trace

router = APIRouter()
tracer = trace.get_tracer(__name__)


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
    stream_request = MlChatStreamRequest(
        user_id=str(current_user.id),
        persona_id=str(active_persona_id),
        session_id=req.session_id,
        message=req.message,
        top_k=10,
        max_toxicity=0.7,
    )

    async def event_generator():
        with tracer.start_as_current_span("ml_chat_stream_request") as span:
            span.set_attribute("user.id", str(current_user.id))
            span.set_attribute("session.id", req.session_id)

            try:
                span.add_event("ml_connection_established")
                async for chunk in ml_chat_service.stream_chat(stream_request):
                    yield chunk
                span.set_status(trace.StatusCode.OK)

            except httpx.RequestError as e:
                span.record_exception(e)
                span.set_status(trace.StatusCode.ERROR, description="ML Server Request Error")
                yield b'data: {"error": "ML_SERVER_UNAVAILABLE"}\n\n'

            except Exception as e:
                span.record_exception(e)
                span.set_status(trace.StatusCode.ERROR, description=str(e))
                raise

    return StreamingResponse(event_generator(), media_type="text/event-stream")
