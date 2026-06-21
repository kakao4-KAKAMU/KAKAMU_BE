from sqlalchemy.orm import Session
from fastapi import HTTPException
from uuid import UUID

from app.models import Comment, LikeLog
from app.service.comment.ml_sync import comment_ml_sync_service


class CommentDeleteService:
    async def delete_comment(self, db: Session, comment_id: int, user_id: UUID) -> None:
        comment = db.query(Comment).filter(Comment.id == comment_id, Comment.status == "ACTIVE").first()
        if not comment:
            raise HTTPException(status_code=404, detail={"code": "COMMENT_NOT_FOUND", "message": "댓글을 찾을 수 없거나 이미 삭제되었습니다."})

        if comment.user_id != user_id:
            raise HTTPException(status_code=403, detail={"code": "FORBIDDEN_COMMENT_DELETE", "message": "본인이 작성한 댓글만 삭제할 수 있습니다."})

        comment.status = "INACTIVE"
        db.query(Comment).filter(Comment.parent_id == comment.id).update({"status": "INACTIVE"})
        db.query(LikeLog).filter(LikeLog.target_type == "COMMENT", LikeLog.target_id == comment.id).update({"is_active": 0})
        db.commit()

        await comment_ml_sync_service.sync_delete(comment_id=comment.id, user_id=user_id)


comment_delete_service = CommentDeleteService()
