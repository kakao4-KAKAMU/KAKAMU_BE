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

router = APIRouter()

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
    # 💡 서비스 레이어에도 persona_id를 함께 전달하여 DB 저장 시 관계를 맺도록 합니다.
    post_id = await post_create_service.create_post(db, post_in, current_user.id, current_persona_id)
    return {"status": "success", "post_id": post_id}