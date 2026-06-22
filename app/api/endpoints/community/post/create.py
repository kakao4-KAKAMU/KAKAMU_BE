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
    """
    새로운 게시물을 작성하고 해시태그 및 멘션을 파싱하여 연결합니다.
    OpenTelemetry를 사용하여 요청 처리 과정을 추적합니다.
    """
    with tracer.start_as_current_span("post_create_request") as span:
        # 요청자 메타데이터를 span에 기록
        span.set_attribute("user.id", str(current_user.id))
        if current_persona_id:
            span.set_attribute("persona.id", str(current_persona_id))

        try:
            # 서비스 레이어에 persona_id를 전달하여 DB에 관계를 저장
            post_id = await post_create_service.create_post(db, post_in, current_user.id, current_persona_id)

            # 생성된 게시글 ID를 기록하고, span 상태를 정상(OK)으로 설정
            span.set_attribute("post.id", post_id)
            span.set_status(trace.StatusCode.OK)

            return {"status": "success", "post_id": post_id}
        except Exception as e:
            # 에러 발생 시 예외 정보를 기록하고, span 상태를 에러(ERROR)로 설정
            span.record_exception(e)
            span.set_status(trace.StatusCode.ERROR, description=str(e))
            raise