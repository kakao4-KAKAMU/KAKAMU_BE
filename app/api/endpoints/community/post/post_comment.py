from fastapi import APIRouter, Depends, Query
from typing import Optional
from sqlalchemy.orm import Session
from uuid import UUID
from app.db.session import get_db
from app.api.deps.auth import get_active_user, get_optional_user
from app.api.deps import get_current_persona
from app.models.user import User
from app.schemas.request.post import CommentCreate
from app.schemas.response.post import CommentListResponse
from app.schemas.response.common import CommentIdResponse
from app.schemas.errors import ERROR_POST_NOT_FOUND_FOR_COMMENT
from app.service.comment.comment_service import comment_service

router = APIRouter()

@router.post(
    "/",
    status_code=201,
    response_model=CommentIdResponse,
    responses={
        404: ERROR_POST_NOT_FOUND_FOR_COMMENT
    },
    summary="댓글(또는 대댓글) 작성"
)
def create_comment(
    post_id: int, 
    comment_in: CommentCreate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_active_user),
    current_persona_id: UUID = Depends(get_current_persona)
):
    """게시물에 댓글(또는 대댓글)을 작성합니다."""
    comment_id = comment_service.create_comment(db, post_id, comment_in, current_user.id, current_persona_id)
    return {"status": "success", "comment_id": comment_id}

@router.get(
    "/",
    response_model=CommentListResponse,
    summary="게시물의 댓글 목록 페이징 조회"
)
def get_comments(
    post_id: int,
    page: int = Query(1, ge=1, description="페이지 번호 (1부터 시작)"),
    size: int = Query(20, ge=1, le=100, description="페이지당 반환할 댓글 수"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """게시물의 댓글 목록을 페이징 처리하여 조회합니다. (비회원 접근 가능) 스포일러 댓글은 내용이 마스킹 처리됩니다."""
    user_id = current_user.id if current_user else None
    comments_data = comment_service.get_comments(db, post_id, user_id, page=page, size=size)
    return {"status": "success", "is_member": current_user is not None, **comments_data}