from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.api.deps import get_current_persona
from app.schemas.post.comment import CommentCreate
from app.service.comment.comment_service import comment_service
from uuid import UUID

router = APIRouter()

@router.post("/", status_code=201)
def create_comment(post_id: int, comment_in: CommentCreate, db: Session = Depends(get_db), persona_id: UUID = Depends(get_current_persona)):
    """게시물에 댓글(또는 대댓글)을 작성합니다."""
    comment_id = comment_service.create_comment(db, post_id, comment_in, persona_id)
    return {"status": "success", "comment_id": comment_id}

@router.get("/")
def get_comments(post_id: int, db: Session = Depends(get_db)):
    """게시물의 댓글 목록을 조회합니다. 스포일러 댓글은 내용이 마스킹 처리됩니다."""
    comments = comment_service.get_comments(db, post_id)
    return {"status": "success", "comments": comments}