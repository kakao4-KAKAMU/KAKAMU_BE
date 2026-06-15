from uuid import UUID
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models import Comment, Post, User, CommentMention
from app.schemas.request.post import CommentCreate
from app.utils.parser import parse_content

class CommentCreateService:
    def create_comment(self, db: Session, post_id: int, comment_in: CommentCreate, user_id: UUID, persona_id: UUID) -> int:
        # 1. 원본 게시물 존재 여부 확인
        post = db.query(Post).filter(Post.id == post_id, Post.status == "ACTIVE").first()
        if not post:
            raise HTTPException(status_code=404, detail={"code": "POST_NOT_FOUND", "message": "게시물을 찾을 수 없거나 삭제되었습니다."})

        # 2. 대댓글인 경우, 부모 댓글 존재 여부 확인
        if comment_in.parent_id:
            parent_comment = db.query(Comment).filter(Comment.id == comment_in.parent_id, Comment.status == "ACTIVE").first()
            if not parent_comment:
                raise HTTPException(status_code=404, detail={"code": "PARENT_COMMENT_NOT_FOUND", "message": "답글을 작성할 원본 댓글을 찾을 수 없습니다."})
            if parent_comment.post_id != post_id:
                raise HTTPException(status_code=400, detail={"code": "COMMENT_POST_MISMATCH", "message": "댓글과 게시물이 일치하지 않습니다."})

        # 3. 댓글 객체 생성 (persona_id 포함)
        new_comment = Comment(
            post_id=post_id,
            user_id=user_id,
            persona_id=persona_id, # 💡 ML 컨텍스트를 위한 페르소나 ID 저장
            parent_id=comment_in.parent_id,
            content=comment_in.content,
            is_spoiler=comment_in.is_spoiler
        )
        db.add(new_comment)
        db.flush()
        

        # 4. 멘션 파싱 및 저장 (기존 로직과 동일)
        _, mentions = parse_content(comment_in.content)
        for mention_str in mentions:
            if "#" not in mention_str: continue
            nickname, tag = mention_str.split("#", 1)
            target_user = db.query(User).filter(User.nickname == nickname, User.tag == tag, User.status == "ACTIVE").first()
            if target_user:
                db.add(CommentMention(comment_id=new_comment.id, user_id=target_user.id))

        db.commit()
        return new_comment.id

comment_create_service = CommentCreateService()