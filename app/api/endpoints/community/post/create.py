from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Any, Optional
from uuid import UUID

from app.db.session import get_db
from app.api.deps import get_current_persona
from app.api.deps.auth import get_active_user
from app.models.user import User
from app.schemas.request.post import PostCreate
from app.schemas.response.common import PostIdResponse
from app.schemas.errors import ERROR_HASHTAG_LIMIT_EXCEEDED
from app.service.post.create_post import post_create_service

# [추가] OpenTelemetry trace 임포트
from opentelemetry import trace

router = APIRouter()

# [추가] 현재 모듈에 대한 tracer 인스턴스 획득
tracer = trace.get_tracer(__name__)


@router.post(
    "/",
    status_code=201,
    response_model=PostIdResponse,
    responses={
        400: ERROR_HASHTAG_LIMIT_EXCEEDED
    },
    summary="새 게시물 작성"
)
async def create_post(
        post_in: PostCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_active_user),
        # 💡 페르소나별 취향/알고리즘 수집을 위해 현재 활성화된 페르소나 정보를 받아옵니다.
        current_persona_id: Optional[UUID] = Depends(get_current_persona)
) -> Any:
    """새로운 게시물을 작성하고 해시태그 및 멘션을 파싱하여 연결합니다."""

    # [추가] 게시글 생성 구간 전체를 추적
    with tracer.start_as_current_span("post_create_request") as span:
        # [추가] 요청자 메타데이터 기록
        span.set_attribute("user.id", str(current_user.id))
        if current_persona_id:
            span.set_attribute("persona.id", str(current_persona_id))

        try:
            # 💡 서비스 레이어에도 persona_id를 함께 전달하여 DB 저장 시 관계를 맺도록 합니다.
            post_id = await post_create_service.create_post(db, post_in, current_user.id, current_persona_id)

            # [추가] 생성된 게시글 ID 기록 및 정상 상태 처리
            span.set_attribute("post.id", post_id)
            span.set_status(trace.StatusCode.OK)

            return {"status": "success", "post_id": post_id}

        except Exception as e:
            # [추가] 에러 발생 시 추적 (FastAPI의 HTTPException 포함)
            span.record_exception(e)
            span.set_status(trace.StatusCode.ERROR, description=str(e))
            raise