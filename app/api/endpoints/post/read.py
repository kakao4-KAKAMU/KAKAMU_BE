from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from uuid import UUID
from app.db.session import get_db
from app.api.deps import get_current_persona
from app.api.deps.auth import get_active_user
from app.models.user import User
from app.service.post.read_post import post_read_service
from app.schemas.response.post import PostListResponse, PostResponse

router = APIRouter()

@router.get("/", response_model=PostListResponse)
def get_posts(
    cursor: Optional[int] = Query(None, description="마지막으로 조회한 게시물의 ID"), 
    limit: int = Query(20, le=100), 
    db: Session = Depends(get_db),
    current_persona_id: UUID = Depends(get_current_persona),
    current_user: User = Depends(get_active_user)
):
    """게시물 피드를 무한 스크롤(Cursor-based) 방식으로 조회합니다."""
    return post_read_service.get_posts(db, current_user.id, cursor, limit)

@router.get("/liked", response_model=PostListResponse)
def get_my_liked_posts(
    cursor: Optional[int] = Query(None, description="마지막으로 조회한 게시물의 ID"), 
    limit: int = Query(20, le=100), 
    db: Session = Depends(get_db),
    current_persona_id: UUID = Depends(get_current_persona),
    current_user: User = Depends(get_active_user)
):
    """
    내가(현재 활성화된 페르소나가) 좋아요를 누른 게시물 목록을 조회합니다.
    차단한 사용자의 게시물은 좋아요를 눌렀었더라도 노출되지 않습니다.
    """
    return post_read_service.get_my_liked_posts(db, current_user.id, cursor, limit)

@router.get("/persona/{target_persona_id}", response_model=PostListResponse)
def get_user_posts(
    target_persona_id: UUID,
    cursor: Optional[int] = Query(None, description="마지막으로 조회한 게시물의 ID"), 
    limit: int = Query(20, le=100), 
    db: Session = Depends(get_db),
    current_persona_id: UUID = Depends(get_current_persona),
    current_user: User = Depends(get_active_user)
):
    """
    특정 페르소나(본인 또는 타인)가 작성한 게시물 목록을 조회합니다.
    """
    return post_read_service.get_user_posts(db, target_persona_id, current_persona_id, current_user.id, cursor, limit)

@router.get("/{post_id}", response_model=PostResponse)
def get_post_detail(
    post_id: int, 
    db: Session = Depends(get_db),
    current_persona_id: UUID = Depends(get_current_persona),
    current_user: User = Depends(get_active_user)
):
    """
    게시물 상세 내용을 조회합니다.
    사용자가 '스포일러 보기'를 클릭해서 들어온 것으로 간주하여 마스킹 없이 원본을 반환합니다.
    """
    return post_read_service.get_post_detail(db, post_id, current_persona_id, current_user.id)