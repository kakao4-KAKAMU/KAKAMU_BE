from sqlalchemy.orm import Session
from fastapi import HTTPException
from uuid import UUID

from app.models import Comment, Persona, CommentMention
from app.schemas.post.comment import CommentUpdate
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
            
            # 본문이 수정되었으므로 기존 멘션 데이터를 삭제하고 재추출
            db.query(CommentMention).filter(CommentMention.comment_id == comment.id).delete()
            
            _, mentions = parse_content(comment_in.content)
            for mention_str in mentions:
                if "#" not in mention_str:
                    continue
                nickname, tag = mention_str.split("#", 1)
                target_persona = db.query(Persona).filter(Persona.nickname == nickname, Persona.tag == tag, Persona.status == "ACTIVE").first()
                if target_persona:
                    db.add(CommentMention(comment_id=comment.id, user_id=target_persona.user_id))
                    
        db.commit()
        return comment.id

comment_update_service = CommentUpdateService()