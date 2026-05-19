from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.api.deps import get_current_persona
from app.schemas.post import CommentCreate
from app.models.models import Comment, Post, Persona, CommentMention
from app.utils.parser import parse_content

router = APIRouter()

@router.post("/{post_id}/comments", status_code=201)
def create_comment(post_id: int, comment_in: CommentCreate, db: Session = Depends(get_db), persona_id: int = Depends(get_current_persona)):
    """게시물에 댓글(또는 대댓글)을 작성합니다."""
    post = db.query(Post).filter(Post.id == post_id, Post.status == "ACTIVE").first()
    if not post:
        raise HTTPException(status_code=404, detail="게시물을 찾을 수 없거나 삭제되었습니다.")
        
    new_comment = Comment(
        post_id=post_id,
        persona_id=persona_id,
        parent_id=comment_in.parent_id,
        content=comment_in.content,
        is_spoiler=comment_in.is_spoiler
    )
    db.add(new_comment)
    db.flush()
    
    # 댓글 내용에서 멘션 파싱 및 연동
    _, mentions = parse_content(comment_in.content)
    for mention_str in mentions:
        nickname, tag = mention_str.split("#")
        target_persona = db.query(Persona).filter(Persona.nickname == nickname, Persona.tag == tag, Persona.status == "ACTIVE").first()
        if target_persona:
            db.add(CommentMention(comment_id=new_comment.id, persona_id=target_persona.id))
            
    db.commit()
    return {"status": "success", "comment_id": new_comment.id}

@router.delete("/comments/{comment_id}")
def delete_comment(comment_id: int, db: Session = Depends(get_db), persona_id: int = Depends(get_current_persona)):
    """댓글을 소프트 삭제합니다. 하위에 대댓글이 있으면 내용만 치환합니다."""
    comment = db.query(Comment).filter(Comment.id == comment_id, Comment.persona_id == persona_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="댓글을 찾을 수 없거나 권한이 없습니다.")
        
    replies_count = db.query(Comment).filter(Comment.parent_id == comment.id, Comment.status == "ACTIVE").count()
    if replies_count > 0:
        comment.content = "삭제된 댓글입니다"
    
    comment.status = "INACTIVE"
    db.commit()
    return {"status": "success"}