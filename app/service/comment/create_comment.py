from sqlalchemy.orm import Session
from fastapi import HTTPException
from uuid import UUID

from app.models import Comment, Post, User, CommentMention
from app.schemas.post.comment import CommentCreate
from app.utils.parser import parse_content

class CommentCreateService:
    def create_comment(self, db: Session, post_id: int, comment_in: CommentCreate, user_id: UUID, persona_id: UUID) -> int:
        post = db.query(Post).filter(Post.id == post_id, Post.status == "ACTIVE").first()
        if not post:
            raise HTTPException(status_code=404, detail={"code": "POST_NOT_FOUND", "message": "게시물을 찾을 수 없거나 삭제되었습니다."})
            
        new_comment = Comment(
            post_id=post_id,
            user_id=user_id,
            persona_id=persona_id, # 어떤 부캐로 썼는지 함께 저장
            parent_id=comment_in.parent_id,
            content=comment_in.content,
            is_spoiler=comment_in.is_spoiler
        )
        db.add(new_comment)
        db.flush()
        
        _, mentions = parse_content(comment_in.content)
        for mention_str in mentions:
            if "#" not in mention_str:
                continue
            nickname, tag = mention_str.split("#", 1)
            target_user = db.query(User).filter(User.nickname == nickname, User.tag == tag, User.status == "ACTIVE").first()
            if target_user:
                db.add(CommentMention(comment_id=new_comment.id, user_id=target_user.id))
                
        db.commit()
        return new_comment.id

comment_create_service = CommentCreateService()