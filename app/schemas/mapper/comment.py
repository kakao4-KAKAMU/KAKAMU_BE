from typing import Optional

from app.models import Comment
from app.models.user import User as UserModel
from app.schemas.base.comment import CommentItem
from app.schemas.mapper.user import UserMapper


class CommentMapper:
    @staticmethod
    def to_comment_item(
        comment: Comment,
        author: Optional[UserModel],
        *,
        is_liked: bool = False,
    ) -> CommentItem:
        return CommentItem(
            id=comment.id,
            parent_id=comment.parent_id,
            user=UserMapper.to_simple_or_anonymous(author),
            content=comment.content,
            is_spoiler=comment.is_spoiler == 1,
            created_at=comment.created_at,
            like_count=comment.like_count,
            is_liked=is_liked,
        )
