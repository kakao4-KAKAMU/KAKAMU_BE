from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_active_user, get_current_persona
from app.db.session import get_db
from app.models.user import User
from app.schemas.errors import ERROR_TARGET_NOT_FOUND, ERROR_UNSUPPORTED_TARGET_TYPE
from app.schemas.request.save import SaveToggleRequest
from app.schemas.response.post import CommentListResponse, PostListResponse
from app.schemas.response.save import SaveToggleResponse, SavedMovieListResponse
from app.service.comment.read_comment import comment_read_service
from app.service.post.read_post import post_read_service
from app.service.save.read_save_service import save_read_service
from app.service.save.save_service import save_service

router = APIRouter()


@router.post(
    "/",
    response_model=SaveToggleResponse,
    responses={
        400: ERROR_UNSUPPORTED_TARGET_TYPE,
        404: ERROR_TARGET_NOT_FOUND,
    },
    summary="게시물/댓글/영화 저장 토글",
)
def savelog(
    req: SaveToggleRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_active_user),
    persona_id: Optional[UUID] = Depends(get_current_persona),
):
    """게시물, 댓글, 영화의 저장 상태를 토글(Save/Unsave)합니다."""
    is_saved = save_service.toggle_save(db, req, current_user.id, persona_id)
    return {"status": "success", "is_saved": is_saved}


@router.get(
    "/posts",
    response_model=PostListResponse,
    summary="내가 저장한 게시물 목록 조회",
)
def get_saved_post(
    cursor: Optional[int] = Query(None, description="마지막으로 조회한 게시물의 ID"),
    limit: int = Query(20, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_active_user),
):
    """내가 저장한 게시물 목록을 조회합니다."""
    return post_read_service.get_my_saved_posts(db, current_user.id, cursor, limit)


@router.get(
    "/comments",
    response_model=CommentListResponse,
    summary="내가 저장한 댓글 목록 조회",
)
def get_saved_comment(
    page: int = Query(1, ge=1),
    size: int = Query(20, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_active_user),
):
    """내가 저장한 댓글 목록을 조회합니다."""
    return comment_read_service.get_my_saved_comments(db, current_user.id, page, size)


@router.get(
    "/movies",
    response_model=SavedMovieListResponse,
    summary="내가 저장한 영화 목록 조회",
)
def get_saved_movie(
    cursor: Optional[int] = Query(None, description="마지막으로 조회한 SaveLog ID"),
    limit: int = Query(20, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_active_user),
):
    """내가 저장한 영화 목록을 조회합니다."""
    return save_read_service.get_my_saved_movies(db, current_user.id, cursor, limit)
