from typing import List, Optional

from app.models import Comment
from app.models.user import User as UserModel
from app.schemas.base.comment import CommentItem
from app.schemas.base.mention import Mention
from app.schemas.mapper.user import UserMapper

SPOILER_MASK = "*** 스포일러로 인해 블라인드 처리되었습니다. 보기 버튼을 눌러 확인하세요. ***"


class CommentMapper:
    @staticmethod
    def to_comment_item(
        comment: Comment,
        author: Optional[UserModel],
        *,
        hashtags: Optional[List[str]] = None,
        mentions: Optional[List[Mention]] = None,
        is_liked: bool = False,
        mask_spoiler: bool = True,
    ) -> CommentItem:
        is_spoiler = comment.is_spoiler == 1
        content = SPOILER_MASK if mask_spoiler and is_spoiler else comment.content
        return CommentItem(
            id=comment.id,
            parent_id=comment.parent_id,
            user=UserMapper.to_simple_or_anonymous(author),
            content=content,
            is_spoiler=is_spoiler,
            created_at=comment.created_at,
            like_count=comment.like_count,
            is_liked=is_liked,
            hashtags=hashtags or [],
            mentions=mentions or [],
        )
