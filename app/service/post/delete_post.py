from uuid import UUID
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models import Post, Comment, LikeLog
from app.service.post.ml_sync import post_ml_sync_service
from app.service.post.redis import post_cache_service

class PostDeleteService:
    async def delete_post(self, db: Session, post_id: int, user_id: UUID, persona_id: UUID) -> None:
        """게시물 소프트 삭제 및 연관 데이터 처리 로직"""
        post = db.query(Post).filter(Post.id == post_id, Post.status == "ACTIVE").first()
        if not post:
            raise HTTPException(status_code=404, detail={"code": "POST_NOT_FOUND", "message": "게시물을 찾을 수 없습니다."})

        if post.user_id != user_id:
            raise HTTPException(status_code=403, detail={"code": "FORBIDDEN_POST_DELETE", "message": "본인이 작성한 게시물만 삭제할 수 있습니다."})

        post.status = "INACTIVE"

        # 게시물 삭제 시 연관된 하위 댓글들도 모두 비활성화 처리 (Soft Delete)
        db.query(Comment).filter(Comment.post_id == post.id).update({"status": "INACTIVE"})

        # 게시물에 달린 좋아요 무효화
        db.query(LikeLog).filter(LikeLog.target_type == "POST", LikeLog.target_id == post.id).update({"is_active": 0})

        db.commit()
        post_cache_service.invalidate_post(post.id)

        await post_ml_sync_service.sync_delete(post_id=post.id, user_id=user_id)

post_delete_service = PostDeleteService()
