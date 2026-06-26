from typing import Dict, List, Optional
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models import Block, Comment, CommentHashtag, CommentMention, Hashtag, LikeLog, User
from app.schemas.base.mention import Mention
from app.schemas.mapper.comment import CommentMapper
from app.schemas.mapper.pagination import PaginationMapper
from app.schemas.response.post import CommentDetailResponse, CommentListResponse


class CommentReadService:
    def _get_mentions_for_comments(self, db: Session, comment_ids: List[int]) -> Dict[int, List[Mention]]:
        if not comment_ids:
            return {}

        mentions_query = db.query(CommentMention.comment_id, User.id, User.nickname, User.tag)\
            .join(User, User.id == CommentMention.user_id)\
            .filter(CommentMention.comment_id.in_(comment_ids), User.status == "ACTIVE").all()

        mentions_map: Dict[int, List[Mention]] = {cid: [] for cid in comment_ids}
        for m in mentions_query:
            mentions_map[m.comment_id].append(Mention(id=m.id, nickname=m.nickname, tag=m.tag))
        return mentions_map

    def _get_hashtags_for_comments(self, db: Session, comment_ids: List[int]) -> Dict[int, List[str]]:
        if not comment_ids:
            return {}

        hashtags_query = db.query(CommentHashtag.comment_id, Hashtag.normalized_keyword)\
            .join(Hashtag, Hashtag.id == CommentHashtag.hashtag_id)\
            .filter(CommentHashtag.comment_id.in_(comment_ids)).all()

        hashtags_map: Dict[int, List[str]] = {cid: [] for cid in comment_ids}
        for h in hashtags_query:
            hashtags_map[h.comment_id].append(h.normalized_keyword)
        return hashtags_map

    def get_comments(
        self,
        db: Session,
        post_id: int,
        current_user_id: Optional[UUID],
        page: int = 1,
        size: int = 20,
    ) -> CommentListResponse:
        offset = (page - 1) * size

        base_query = db.query(Comment, User).join(User, Comment.user_id == User.id).filter(
            Comment.post_id == post_id,
            Comment.status == "ACTIVE"
        )

        if current_user_id:
            blocked_by_me = select(Block.blocked_id).where(Block.blocker_id == current_user_id)
            blocking_me = select(Block.blocker_id).where(Block.blocked_id == current_user_id)
            base_query = base_query.filter(
                Comment.user_id.notin_(blocked_by_me),
                Comment.user_id.notin_(blocking_me)
            )

        total_count = base_query.with_entities(func.count(Comment.id)).scalar() or 0

        comments = base_query.order_by(Comment.created_at.desc()).offset(offset).limit(size).all()

        comment_ids = [c.id for c, _ in comments]
        mentions_map = self._get_mentions_for_comments(db, comment_ids)
        hashtags_map = self._get_hashtags_for_comments(db, comment_ids)

        liked_comment_ids = set()
        if current_user_id and comment_ids:
            liked_logs = db.query(LikeLog.target_id).filter(
                LikeLog.user_id == current_user_id,
                LikeLog.target_type == "COMMENT",
                LikeLog.target_id.in_(comment_ids),
                LikeLog.is_active == 1
            ).all()
            liked_comment_ids = {log[0] for log in liked_logs}

        items = [
            CommentMapper.to_comment_item(
                c,
                author,
                hashtags=hashtags_map.get(c.id, []),
                mentions=mentions_map.get(c.id, []),
                is_liked=c.id in liked_comment_ids,
            )
            for c, author in comments
        ]

        return CommentListResponse(
            items=items,
            meta=PaginationMapper.build_page_meta(
                total_count=total_count,
                current_page=page,
                page_size=size,
            ),
        )

    def get_comment_detail(self, db: Session, comment_id: int, current_user_id: Optional[UUID]) -> CommentDetailResponse:
        comment = db.query(Comment).filter(Comment.id == comment_id, Comment.status == "ACTIVE").first()
        if not comment:
            raise HTTPException(status_code=404, detail={"code": "COMMENT_NOT_FOUND", "message": "댓글을 찾을 수 없습니다."})

        if current_user_id:
            is_blocked = db.query(Block).filter(
                or_(
                    (Block.blocker_id == current_user_id) & (Block.blocked_id == comment.user_id),
                    (Block.blocker_id == comment.user_id) & (Block.blocked_id == current_user_id)
                )
            ).first()
            if is_blocked:
                raise HTTPException(status_code=403, detail={"code": "FORBIDDEN_BLOCKED_COMMENT", "message": "차단된 사용자의 댓글입니다."})

        mentions_map = self._get_mentions_for_comments(db, [comment.id])
        hashtags_map = self._get_hashtags_for_comments(db, [comment.id])

        author = db.query(User).filter(User.id == comment.user_id).first()

        is_liked = False
        if current_user_id:
            is_liked = db.query(LikeLog).filter(
                LikeLog.user_id == current_user_id,
                LikeLog.target_type == "COMMENT",
                LikeLog.target_id == comment.id,
                LikeLog.is_active == 1
            ).first() is not None

        return CommentMapper.to_comment_item(
            comment,
            author,
            hashtags=hashtags_map.get(comment.id, []),
            mentions=mentions_map.get(comment.id, []),
            is_liked=is_liked,
        )


comment_read_service = CommentReadService()
