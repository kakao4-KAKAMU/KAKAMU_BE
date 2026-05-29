from sqlalchemy.orm import Session
from fastapi import HTTPException
from uuid import UUID
from typing import List, Dict, Any

from app.models import Comment, Post, Persona, CommentMention, LikeLog
from app.schemas.post.comment import CommentCreate
from app.utils.parser import parse_content

class CommentService:
    def create_comment(self, db: Session, post_id: int, comment_in: CommentCreate, persona_id: UUID) -> int:
        post = db.query(Post).filter(Post.id == post_id, Post.status == "ACTIVE").first()
        if not post:
            raise HTTPException(status_code=404, detail={"code": "POST_NOT_FOUND", "message": "게시물을 찾을 수 없거나 삭제되었습니다."})
            
        new_comment = Comment(
            post_id=post_id,
            persona_id=persona_id,
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
            target_persona = db.query(Persona).filter(Persona.nickname == nickname, Persona.tag == tag, Persona.status == "ACTIVE").first()
            if target_persona:
                db.add(CommentMention(comment_id=new_comment.id, persona_id=target_persona.id))
                
        db.commit()
        return new_comment.id

    def get_comments(self, db: Session, post_id: int) -> List[Dict[str, Any]]:
        comments = db.query(Comment).filter(Comment.post_id == post_id, Comment.status == "ACTIVE").order_by(Comment.created_at.asc()).all()
        result = []
        for c in comments:
            author = c.persona
            author_name = "알 수 없음" if not author or author.status == "DELETED" else f"{author.nickname}#{author.tag}"
            is_spoiler = c.is_spoiler == 1
            result.append({
                "id": c.id, "parent_id": c.parent_id, "author_id": None if not author or author.status == "DELETED" else author.id,
                "author": author_name, "content": "*** 스포일러로 인해 블라인드 처리되었습니다. 보기 버튼을 눌러 확인하세요. ***" if is_spoiler else c.content,
                "is_spoiler": is_spoiler, "created_at": c.created_at
            })
        return result

    def delete_comment(self, db: Session, comment_id: int, persona_id: UUID) -> None:
        comment = db.query(Comment).filter(Comment.id == comment_id, Comment.persona_id == persona_id).first()
        if not comment:
            raise HTTPException(status_code=404, detail={"code": "COMMENT_NOT_FOUND_OR_FORBIDDEN", "message": "댓글을 찾을 수 없거나 권한이 없습니다."})
            
        comment.status = "INACTIVE"
        db.query(Comment).filter(Comment.parent_id == comment.id).update({"status": "INACTIVE"})
        db.query(LikeLog).filter(LikeLog.target_type == "COMMENT", LikeLog.target_id == comment.id).update({"is_active": 0})
        db.commit()

    def get_comment_detail(self, db: Session, comment_id: int) -> Dict[str, Any]:
        comment = db.query(Comment).filter(Comment.id == comment_id, Comment.status == "ACTIVE").first()
        if not comment:
            raise HTTPException(status_code=404, detail={"code": "COMMENT_NOT_FOUND", "message": "댓글을 찾을 수 없습니다."})
        return {"id": comment.id, "content": comment.content}

comment_service = CommentService()
