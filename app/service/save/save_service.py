from typing import Optional
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import Comment, Movie, Post, SaveLog, PostStatus, CommentStatus
from app.schemas.request.save import SaveToggleRequest
from app.service.movie.get_movie import movie_read_service
from app.service.save import save_lookup


class SaveService:
    def toggle_save(
        self,
        db: Session,
        req: SaveToggleRequest,
        user_id: UUID,
        persona_id: Optional[UUID],
    ) -> bool:
        """게시물/댓글/영화 저장을 토글(Save/Unsave)합니다."""
        if req.target_type == "POST":
            target = db.query(Post).filter(Post.id == req.target_id, Post.status == PostStatus.ACTIVE).first()
            save_log = self._find_save_log(db, user_id, req.target_type, target_id=req.target_id)
        elif req.target_type == "COMMENT":
            target = db.query(Comment).filter(Comment.id == req.target_id, Comment.status == CommentStatus.ACTIVE).first()
            save_log = self._find_save_log(db, user_id, req.target_type, target_id=req.target_id)
        else:
            target = movie_read_service.base_query(db).filter(Movie.id == req.movie_id).first()
            save_log = self._find_save_log(db, user_id, req.target_type, movie_id=req.movie_id)

        if not target:
            raise HTTPException(
                status_code=404,
                detail={"code": "TARGET_NOT_FOUND", "message": "대상을 찾을 수 없습니다."},
            )

        if save_log:
            save_log.is_active = 0 if save_log.is_active == 1 else 1
            is_saved = save_log.is_active == 1
            if is_saved:
                save_log.persona_id = persona_id
        else:
            save_log = SaveLog(
                user_id=user_id,
                persona_id=persona_id,
                target_type=req.target_type,
                target_id=req.target_id if req.target_type != "MOVIE" else None,
                movie_id=req.movie_id if req.target_type == "MOVIE" else None,
                is_active=1,
            )
            db.add(save_log)
            is_saved = True

        db.commit()
        return is_saved

    @staticmethod
    def _find_save_log(
        db: Session,
        user_id: UUID,
        target_type: str,
        *,
        target_id: Optional[int] = None,
        movie_id: Optional[UUID] = None,
    ) -> Optional[SaveLog]:
        query = db.query(SaveLog).filter(
            SaveLog.user_id == user_id,
            SaveLog.target_type == target_type,
        )
        if movie_id is not None:
            query = query.filter(SaveLog.movie_id == movie_id)
        else:
            query = query.filter(SaveLog.target_id == target_id)
        return query.first()


save_service = SaveService()

get_saved_target_ids = save_lookup.get_saved_target_ids
is_movie_saved = save_lookup.is_movie_saved
