from sqlalchemy.orm import Session
from fastapi import HTTPException
from uuid import UUID

from app.models import Comment, User, CommentMention, Hashtag, CommentHashtag
from app.schemas.request.post import CommentUpdate
from app.utils.parser import parse_content

class CommentUpdateService:
    def update_comment(self, db: Session, comment_id: int, comment_in: CommentUpdate, user_id: UUID) -> int:
        comment = db.query(Comment).filter(Comment.id == comment_id, Comment.status == "ACTIVE").first()
        if not comment:
            raise HTTPException(status_code=404, detail={"code": "COMMENT_NOT_FOUND", "message": "댓글을 찾을 수 없거나 삭제되었습니다."})
            
        # 본인 작성 여부 검증
        if comment.user_id != user_id:
            raise HTTPException(status_code=403, detail={"code": "FORBIDDEN_COMMENT_UPDATE", "message": "본인이 작성한 댓글만 수정할 수 있습니다."})

        if comment_in.is_spoiler is not None:
            comment.is_spoiler = comment_in.is_spoiler

        if comment_in.content is not None and comment_in.content != comment.content:
            comment.content = comment_in.content
            
            # 본문이 수정되었으므로 기존 멘션/해시태그 데이터를 삭제하고 재추출
            db.query(CommentMention).filter(CommentMention.comment_id == comment.id).delete()
            db.query(CommentHashtag).filter(CommentHashtag.comment_id == comment.id).delete()
            
            hashtags, mentions = parse_content(comment_in.content)
            
            if len(hashtags) > 10:
                raise HTTPException(status_code=400, detail={"code": "HASHTAG_LIMIT_EXCEEDED", "message": "해시태그는 최대 10개까지만 등록할 수 있습니다."})

            for clean_keyword in hashtags:
                hashtag_obj = db.query(Hashtag).filter(Hashtag.normalized_keyword == clean_keyword).first()
                if not hashtag_obj:
                    hashtag_obj = Hashtag(normalized_keyword=clean_keyword)
                    db.add(hashtag_obj)
                    db.flush()
                db.add(CommentHashtag(comment_id=comment.id, hashtag_id=hashtag_obj.id))

            for mention_str in mentions:
                if "#" not in mention_str:
                    continue
                nickname, tag = mention_str.split("#", 1)
                target_user = db.query(User).filter(User.nickname == nickname, User.tag == tag, User.status == "ACTIVE").first()
                if target_user:
                    db.add(CommentMention(comment_id=comment.id, user_id=target_user.id))
                    
        db.commit()
        return comment.id

comment_update_service = CommentUpdateService()