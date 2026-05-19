from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.api.deps import get_current_persona
from app.schemas.post.comment import CommentCreate
from app.models import Comment, Post, Persona, CommentMention
from app.utils.parser import parse_content

router = APIRouter()

@router.post("/", status_code=201)
@router.post("/", status_code=201)
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

@router.get("/")
def get_comments(post_id: int, db: Session = Depends(get_db)):
    """게시물의 댓글 목록을 조회합니다. 스포일러 댓글은 내용이 마스킹 처리됩니다."""
    comments = db.query(Comment).filter(
        Comment.post_id == post_id, 
        Comment.status == "ACTIVE"
    ).order_by(Comment.created_at.asc()).all()
    
    result = []
    for c in comments:
        author = c.persona
        author_name = "알 수 없음" if not author or author.status == "DELETED" else f"{author.nickname}#{author.tag}"
        
        is_spoiler = c.is_spoiler == 1
        
        result.append({
            "id": c.id,
            "parent_id": c.parent_id,
            "author": author_name,
            "content": "*** 스포일러 주의! 클릭하여 확인하세요. ***" if is_spoiler else c.content,
            "is_spoiler": is_spoiler,
            "created_at": c.created_at
        })
    return {"status": "success", "comments": result}