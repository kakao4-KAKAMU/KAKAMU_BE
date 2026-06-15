from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.api.deps import get_active_user
from app.models.user import User
from app.schemas.response.post import CommentDetailResponse
from app.schemas.response.common import SuccessResponse
from app.schemas.errors import (
    ERROR_COMMENT_NOT_FOUND,
    ERROR_FORBIDDEN_COMMENT_DELETE,
    ERROR_FORBIDDEN_BLOCKED_COMMENT
)
from app.service.comment.comment_service import comment_service

router = APIRouter()

@router.delete(
    "/{comment_id}",
    response_model=SuccessResponse,
    responses={
        403: ERROR_FORBIDDEN_COMMENT_DELETE,
        404: ERROR_COMMENT_NOT_FOUND
    }
)
def delete_comment(comment_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_active_user)):
    """댓글을 소프트 삭제합니다. 삭제 시 하위 대댓글도 모두 함께 비활성화(INACTIVE) 처리됩니다."""
    comment_service.delete_comment(db, comment_id, current_user.id)
    return {"status": "success"}

@router.get(
    "/{comment_id}",
    response_model=CommentDetailResponse,
    responses={
        403: ERROR_FORBIDDEN_BLOCKED_COMMENT,
        404: ERROR_COMMENT_NOT_FOUND
    }
)
def get_comment_detail(comment_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_active_user)):
    """사용자가 댓글의 '스포일러 보기'를 클릭했을 때 원본 내용을 반환합니다."""
    return comment_service.get_comment_detail(db, comment_id, current_user.id)