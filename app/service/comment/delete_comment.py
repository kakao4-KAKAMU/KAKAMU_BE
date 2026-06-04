from sqlalchemy.orm import Session
from fastapi import HTTPException
from uuid import UUID

from app.models import Comment, LikeLog

class CommentDeleteService:
    def delete_comment(self, db: Session, comment_id: int, persona_id: UUID) -> None:
        # 1. 댓글의 존재 여부 및 활성 상태를 먼저 확인
        comment = db.query(Comment).filter(Comment.id == comment_id, Comment.status == "ACTIVE").first()
        if not comment:
            raise HTTPException(status_code=404, detail={"code": "COMMENT_NOT_FOUND", "message": "댓글을 찾을 수 없거나 이미 삭제되었습니다."})
            
        # 2. 본인이 작성한 댓글인지 권한 검증 (명확한 에러 코드 분리)
        if comment.persona_id != persona_id:
            raise HTTPException(status_code=403, detail={"code": "FORBIDDEN_COMMENT_DELETE", "message": "본인이 작성한 댓글만 삭제할 수 있습니다."})
            
        comment.status = "INACTIVE"
        db.query(Comment).filter(Comment.parent_id == comment.id).update({"status": "INACTIVE"})
        db.query(LikeLog).filter(LikeLog.target_type == "COMMENT", LikeLog.target_id == comment.id).update({"is_active": 0})
        db.commit()

comment_delete_service = CommentDeleteService()