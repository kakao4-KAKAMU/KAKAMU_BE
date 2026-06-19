from typing import List, Optional

from app.models import Comment
from app.models.user import User as UserModel
from app.schemas.base.comment import CommentItem
from app.schemas.base.mention import Mention
from app.schemas.mapper.user import UserMapper

class CommentMapper:
    @staticmethod
    def to_comment_item(
        comment: Comment,
        author: Optional[UserModel],
        *,
        hashtags: Optional[List[str]] = None,
        mentions: Optional[List[Mention]] = None,
        is_liked: bool = False,
    ) -> CommentItem:
        is_spoiler = comment.is_spoiler == 1
        return CommentItem(
            id=comment.id,
            parent_id=comment.parent_id,
            user=UserMapper.to_simple_or_anonymous(author),
            content=comment.content,
            is_spoiler=is_spoiler,
            created_at=comment.created_at,
            like_count=comment.like_count,
            is_liked=is_liked,
            hashtags=hashtags or [],
            mentions=mentions or [],
        )
