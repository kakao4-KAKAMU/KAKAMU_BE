from uuid import UUID

from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models import Comment, Post, User, CommentMention, Hashtag, CommentHashtag, PostStatus, UserStatus, CommentStatus
from app.schemas.request.post import CommentCreate
from app.service.comment.ml_sync import comment_ml_sync_service
from app.service.post.redis import post_cache_service
from app.utils.parser import parse_content


class CommentCreateService:
    async def create_comment(
        self,
        db: Session,
        post_id: int,
        comment_in: CommentCreate,
        user_id: UUID,
        persona_id: UUID,
    ) -> int:
        post = db.query(Post).filter(Post.id == post_id, Post.status == PostStatus.ACTIVE).first()
        if not post:
            raise HTTPException(status_code=404, detail={"code": "POST_NOT_FOUND", "message": "게시물을 찾을 수 없거나 삭제되었습니다."})

        parent_id = comment_in.parent_id if comment_in.parent_id else None

        if parent_id:
            parent_comment = db.query(Comment).filter(Comment.id == parent_id, Comment.status == CommentStatus.ACTIVE).first()
            if not parent_comment:
                raise HTTPException(status_code=404, detail={"code": "PARENT_COMMENT_NOT_FOUND", "message": "답글을 작성할 원본 댓글을 찾을 수 없습니다."})
            if parent_comment.post_id != post_id:
                raise HTTPException(status_code=400, detail={"code": "COMMENT_POST_MISMATCH", "message": "댓글과 게시물이 일치하지 않습니다."})

        new_comment = Comment(
            post_id=post_id,
            user_id=user_id,
            persona_id=persona_id,
            parent_id=parent_id,
            content=comment_in.content,
            is_spoiler=comment_in.is_spoiler,
        )
        db.add(new_comment)
        db.flush()

        hashtags, mentions = parse_content(comment_in.content)

        if len(hashtags) > 10:
            raise HTTPException(status_code=400, detail={"code": "HASHTAG_LIMIT_EXCEEDED", "message": "해시태그는 최대 10개까지만 등록할 수 있습니다."})

        for clean_keyword in hashtags:
            hashtag_obj = db.query(Hashtag).filter(Hashtag.normalized_keyword == clean_keyword).first()
            if not hashtag_obj:
                hashtag_obj = Hashtag(normalized_keyword=clean_keyword)
                db.add(hashtag_obj)
                db.flush()
            db.add(CommentHashtag(comment_id=new_comment.id, hashtag_id=hashtag_obj.id))

        for mention_str in mentions:
            if "#" not in mention_str:
                continue
            nickname, tag = mention_str.split("#", 1)
            target_user = db.query(User).filter(User.nickname == nickname, User.tag == tag, User.status == UserStatus.ACTIVE).first()
            if target_user:
                db.add(CommentMention(comment_id=new_comment.id, user_id=target_user.id))

        db.commit()
        post_cache_service.sync_comment_count(db, post_id, delta=1)

        await comment_ml_sync_service.sync_create(
            db,
            comment_id=new_comment.id,
            post_id=post_id,
            user_id=user_id,
            persona_id=persona_id,
            comment_in=comment_in,
        )
        return int(new_comment.id) if new_comment.id else 0


comment_create_service = CommentCreateService()
