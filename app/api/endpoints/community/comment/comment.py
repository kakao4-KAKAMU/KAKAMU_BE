from fastapi import APIRouter, Depends
from typing import Optional
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.api.deps.auth import get_active_user, get_optional_user
from app.models.user import User
from app.schemas.request.post import CommentUpdate
from app.schemas.response.post import CommentDetailResponse
from app.schemas.response.common import SuccessResponse, CommentIdResponse
from app.schemas.errors import (
    ERROR_COMMENT_NOT_FOUND,
    ERROR_FORBIDDEN_COMMENT_DELETE,
    ERROR_FORBIDDEN_COMMENT_UPDATE,
    ERROR_FORBIDDEN_BLOCKED_COMMENT,
    ERROR_HASHTAG_LIMIT_EXCEEDED,
)
from app.service.comment.comment_service import comment_service

router = APIRouter()

@router.put(
    "/{comment_id}",
    response_model=CommentIdResponse,
    responses={
        400: ERROR_HASHTAG_LIMIT_EXCEEDED,
        403: ERROR_FORBIDDEN_COMMENT_UPDATE,
        404: ERROR_COMMENT_NOT_FOUND,
    },
    summary="댓글 수정",
)
async def update_comment(
    comment_id: int,
    comment_in: CommentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_active_user),
):
    """댓글 내용 및 스포일러 여부를 수정합니다. 본인이 작성한 댓글만 수정할 수 있습니다."""
    updated_comment_id = await comment_service.update_comment(db, comment_id, comment_in, current_user.id)
    return {"status": "success", "comment_id": updated_comment_id}

@router.delete(
    "/{comment_id}",
    response_model=SuccessResponse,
    responses={
        403: ERROR_FORBIDDEN_COMMENT_DELETE,
        404: ERROR_COMMENT_NOT_FOUND
    },
    summary="댓글 삭제 (소프트 삭제)"
)
async def delete_comment(comment_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_active_user)):
    """댓글을 소프트 삭제합니다. 삭제 시 하위 대댓글도 모두 함께 비활성화(INACTIVE) 처리됩니다."""
    await comment_service.delete_comment(db, comment_id, current_user.id)
    return {"status": "success"}

@router.get(
    "/{comment_id}",
    response_model=CommentDetailResponse,
    responses={
        403: ERROR_FORBIDDEN_BLOCKED_COMMENT,
        404: ERROR_COMMENT_NOT_FOUND
    },
    summary="단일 댓글 상세(스포일러 원본) 조회"
)
def get_comment_detail(comment_id: int, db: Session = Depends(get_db), current_user: Optional[User] = Depends(get_optional_user)):
    """사용자가 댓글의 '스포일러 보기'를 클릭했을 때 원본 내용을 반환합니다. (비회원 접근 가능)"""
    user_id = current_user.id if current_user else None
    return comment_service.get_comment_detail(db, comment_id, user_id)

