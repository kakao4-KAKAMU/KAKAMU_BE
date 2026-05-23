from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from app.db.session import get_db
from app.api.deps import get_current_persona
from app.models import Comment, LikeLog

router = APIRouter()

@router.delete("/{comment_id}")
def delete_comment(comment_id: int, db: Session = Depends(get_db), persona_id: UUID = Depends(get_current_persona)):
    """댓글을 소프트 삭제합니다. 삭제 시 하위 대댓글도 모두 함께 비활성화(INACTIVE) 처리됩니다."""
    comment = db.query(Comment).filter(Comment.id == comment_id, Comment.persona_id == persona_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="댓글을 찾을 수 없거나 권한이 없습니다.")
        
    # 부모 댓글 및 연관된 하위 대댓글 모두 비활성화
    comment.status = "INACTIVE"
    db.query(Comment).filter(Comment.parent_id == comment.id).update({"status": "INACTIVE"})
    
    # 댓글에 달린 좋아요 무효화
    db.query(LikeLog).filter(LikeLog.target_type == "COMMENT", LikeLog.target_id == comment.id).update({"is_active": 0})
        
    db.commit()
    return {"status": "success"}

@router.get("/{comment_id}")
def get_comment_detail(comment_id: int, db: Session = Depends(get_db)):
    """사용자가 댓글의 '스포일러 보기'를 클릭했을 때 원본 내용을 반환합니다."""
    comment = db.query(Comment).filter(Comment.id == comment_id, Comment.status == "ACTIVE").first()
    if not comment:
        raise HTTPException(status_code=404, detail="댓글을 찾을 수 없습니다.")
    return {"id": comment.id, "content": comment.content}