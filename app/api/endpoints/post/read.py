from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.models import Post

router = APIRouter()

@router.get("/")
def get_posts(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    """게시물 피드를 조회합니다. 스포일러 게시물은 본문과 제목이 마스킹됩니다."""
    posts = db.query(Post).filter(Post.status == "ACTIVE").order_by(Post.created_at.desc()).offset(skip).limit(limit).all()
    
    result = []
    for post in posts:
        author = post.persona
        # 페르소나 익명화 정책 반영
        author_name = "알 수 없음" if author.status == "DELETED" else f"{author.nickname}#{author.tag}"
        
        # 스포일러 마스킹 로직
        is_spoiler = post.is_spoiler == 1
        
        result.append({
            "id": post.id,
            "author": author_name,
            "author_image": None if author.status == "DELETED" else author.profile_image_url,
            "title": "*** 스포일러가 포함된 제목입니다 ***" if is_spoiler else post.title,
            "content": "*** 스포일러로 인해 블라인드 처리되었습니다. 보기 버튼을 눌러 확인하세요. ***" if is_spoiler else post.content,
            "image_urls": [] if is_spoiler else post.image_urls,
            "is_spoiler": is_spoiler,
            "created_at": post.created_at,
            # 영화 태그는 스포일러 상관없이 가시 정보로 노출 (정책 반영)
            "movies": [{"id": m.id, "title": m.title} for m in post.movies]
        })
    return result

@router.get("/{post_id}")
def get_post_detail(post_id: int, db: Session = Depends(get_db)):
    """
    게시물 상세 내용을 조회합니다.
    사용자가 '스포일러 보기'를 클릭해서 들어온 것으로 간주하여 마스킹 없이 원본을 반환합니다.
    """
    post = db.query(Post).filter(Post.id == post_id, Post.status == "ACTIVE").first()
    if not post:
        raise HTTPException(status_code=404, detail="게시물을 찾을 수 없습니다.")
        
    author = post.persona
    author_name = "알 수 없음" if author.status == "DELETED" else f"{author.nickname}#{author.tag}"
    
    return {"id": post.id, "author": author_name, "title": post.title, "content": post.content, "image_urls": post.image_urls, "is_spoiler": post.is_spoiler == 1}