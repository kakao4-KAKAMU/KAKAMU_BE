from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from uuid import UUID
from app.db.session import get_db
from app.api.deps import get_current_persona
from app.service.comment.comment_service import comment_service

router = APIRouter()

@router.delete("/{comment_id}")
def delete_comment(comment_id: int, db: Session = Depends(get_db), persona_id: UUID = Depends(get_current_persona)):
    """댓글을 소프트 삭제합니다. 삭제 시 하위 대댓글도 모두 함께 비활성화(INACTIVE) 처리됩니다."""
    comment_service.delete_comment(db, comment_id, persona_id)
    return {"status": "success"}

@router.get("/{comment_id}")
def get_comment_detail(comment_id: int, db: Session = Depends(get_db)):
    """사용자가 댓글의 '스포일러 보기'를 클릭했을 때 원본 내용을 반환합니다."""
    return comment_service.get_comment_detail(db, comment_id)