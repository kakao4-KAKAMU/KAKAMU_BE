import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from uuid import UUID
from sqlalchemy.orm import Session

from app.api.deps import get_current_persona, get_active_user
from app.db.session import get_db
from app.models import User
from app.schemas.errors import ERROR_ML_SERVER_UNAVAILABLE
from app.schemas.request.chat import ChatRequest
from app.schemas.request.ml.chat import MlChatStreamRequest
from app.schemas.response.chat import ChatSession, ChatSessionHistoryResponse
from app.service.ml import ml_chat_service

from opentelemetry import trace
from app.core.logging import logger

router = APIRouter()
tracer = trace.get_tracer(__name__)


def _raise_ml_unavailable() -> None:
    raise HTTPException(
        status_code=503,
        detail={
            "code": "ML_SERVER_UNAVAILABLE",
            "message": "추천 서버(ML/VLLM)와 통신할 수 없거나 응답이 지연되고 있습니다.",
        },
    )


@router.get(
    "/list",
    response_model=list[ChatSession],
    responses={503: ERROR_ML_SERVER_UNAVAILABLE},
    summary="채팅 세션 목록 조회",
)
async def list_chat_sessions(
    cursor: int | None = Query(default=None, ge=1, description="페이지 커서"),
    limit: int = Query(default=20, ge=1, le=200, description="조회 개수"),
    current_user: User = Depends(get_active_user),
):
    try:
        return await ml_chat_service.list_sessions_for_user(
            current_user.id,
            cursor=cursor,
            limit=limit,
        )
    except httpx.RequestError as e:
        logger.error(f"ML Server Request Error: {e}")
        _raise_ml_unavailable()


@router.get(
    "/history/{session_id}",
    response_model=ChatSessionHistoryResponse,
    responses={503: ERROR_ML_SERVER_UNAVAILABLE},
    summary="채팅 세션 메시지 이력 조회",
)
async def get_chat_session_history(
    session_id: str,
    cursor: int | None = Query(default=None, ge=1, description="페이지 커서"),
    limit: int = Query(default=20, ge=1, le=200, description="조회 개수"),
    current_user: User = Depends(get_active_user),
):
    try:
        return await ml_chat_service.get_session_history_for_user(
            current_user.id,
            session_id,
            cursor=cursor,
            limit=limit,
        )
    except httpx.RequestError as e:
        logger.error(f"ML Server Request Error: {e}")
        _raise_ml_unavailable()


@router.post(
    "/completions",
    responses={503: ERROR_ML_SERVER_UNAVAILABLE},
    summary="챗봇 텍스트 스트리밍 생성",
)
async def chat_with_vllm(
    req: ChatRequest,
    current_user: User = Depends(get_active_user),
    active_persona_id: UUID = Depends(get_current_persona),
    db: Session = Depends(get_db),
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
                async for chunk in ml_chat_service.stream_chat(db, current_user.id, stream_request):
                    yield chunk
                span.set_status(trace.StatusCode.OK)

            except httpx.RequestError as e:
                span.record_exception(e)
                span.set_status(
                    trace.StatusCode.ERROR, description="ML Server Request Error"
                )
                yield b'data: {"error": "ML_SERVER_UNAVAILABLE"}\n\n'

            except Exception as e:
                span.record_exception(e)
                span.set_status(trace.StatusCode.ERROR, description=str(e))
                raise

    return StreamingResponse(event_generator(), media_type="text/event-stream")
