from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from uuid import UUID
from app.db.session import get_db
from app.models import Post, Hashtag, PostHashtag, Comment, LikeLog, Block
from app.api.deps import get_current_persona

router = APIRouter()

@router.get("/")
def get_posts(
    cursor: Optional[int] = Query(None, description="마지막으로 조회한 게시물의 ID"), 
    limit: int = Query(20, le=100), 
    db: Session = Depends(get_db),
    current_persona_id: UUID = Depends(get_current_persona)
):
    """게시물 피드를 무한 스크롤(Cursor-based) 방식으로 조회합니다. 스포일러 게시물은 본문과 제목이 마스킹됩니다."""
    
    # 1. 내가 차단한 페르소나와 나를 차단한 페르소나의 ID 목록 조회
    blocked_by_me = db.query(Block.blocked_id).filter(Block.blocker_id == current_persona_id).all()
    blocking_me = db.query(Block.blocker_id).filter(Block.blocked_id == current_persona_id).all()
    excluded_persona_ids = [b[0] for b in blocked_by_me] + [b[0] for b in blocking_me]

    query = db.query(Post).filter(Post.status == "ACTIVE")
    
    # 2. 차단 대상의 게시물은 피드에서 제외
    if excluded_persona_ids:
        query = query.filter(Post.persona_id.notin_(excluded_persona_ids))

    if cursor:
        query = query.filter(Post.id < cursor)
    
    posts = query.order_by(Post.id.desc()).limit(limit).all()
    
    result = []
    for post in posts:
        author = post.persona
        # 페르소나 익명화 정책 반영
        author_name = "알 수 없음" if author.status == "DELETED" else f"{author.nickname}#{author.tag}"
        
        # 스포일러 마스킹 로직
        is_spoiler = post.is_spoiler == 1
        
        # 해시태그 목록 조회
        tags = db.query(Hashtag.normalized_keyword).join(
            PostHashtag, Hashtag.id == PostHashtag.hashtag_id
        ).filter(PostHashtag.post_id == post.id).all()
        hashtag_list = [t[0] for t in tags]
        
        # 통계 데이터 (좋아요, 댓글 수) 조회
        like_count = db.query(LikeLog).filter(
            LikeLog.target_type == "POST", LikeLog.target_id == post.id, LikeLog.is_active == 1
        ).count()
        
        comment_count = db.query(Comment).filter(
            Comment.post_id == post.id, Comment.status == "ACTIVE"
        ).count()

        result.append({
            "id": post.id,
            "author_id": None if author.status == "DELETED" else author.id,
            "author": author_name,
            "author_image": None if author.status == "DELETED" else author.profile_image_url,
            "title": "*** 스포일러가 포함된 제목입니다 ***" if is_spoiler else post.title,
            "content": "*** 스포일러로 인해 블라인드 처리되었습니다. 보기 버튼을 눌러 확인하세요. ***" if is_spoiler else post.content,
            "image_urls": [] if is_spoiler else post.image_urls,
            "is_spoiler": is_spoiler,
            "created_at": post.created_at,
            # 영화 태그는 스포일러 상관없이 가시 정보로 노출 (정책 반영)
            "movies": [{"id": m.id, "title": m.title} for m in post.movies],
            "hashtags": hashtag_list,
            "like_count": like_count,
            "comment_count": comment_count
        })
    
    next_cursor = result[-1]["id"] if result else None
    return {
        "items": result,
        "next_cursor": next_cursor,
        "has_next": len(result) == limit
    }

@router.get("/liked")
def get_my_liked_posts(
    cursor: Optional[int] = Query(None, description="마지막으로 조회한 게시물의 ID"), 
    limit: int = Query(20, le=100), 
    db: Session = Depends(get_db),
    current_persona_id: UUID = Depends(get_current_persona)
):
    """
    내가(현재 활성화된 페르소나가) 좋아요를 누른 게시물 목록을 조회합니다.
    차단한 사용자의 게시물은 좋아요를 눌렀었더라도 노출되지 않습니다.
    """
    
    # 1. 차단한/차단당한 페르소나 제외 로직
    blocked_by_me = db.query(Block.blocked_id).filter(Block.blocker_id == current_persona_id).all()
    blocking_me = db.query(Block.blocker_id).filter(Block.blocked_id == current_persona_id).all()
    excluded_persona_ids = [b[0] for b in blocked_by_me] + [b[0] for b in blocking_me]

    # 2. LikeLog에서 내가 좋아요(is_active=1)한 게시물의 ID만 추출 (Subquery)
    liked_post_ids_subquery = db.query(LikeLog.target_id).filter(
        LikeLog.persona_id == current_persona_id,
        LikeLog.target_type == "POST",
        LikeLog.is_active == 1
    ).subquery()

    # 3. 추출한 ID에 해당하는 게시물만 필터링하여 조회
    query = db.query(Post).filter(
        Post.id.in_(liked_post_ids_subquery),
        Post.status == "ACTIVE"
    )
    
    if excluded_persona_ids:
        query = query.filter(Post.persona_id.notin_(excluded_persona_ids))

    if cursor:
        query = query.filter(Post.id < cursor)
    
    posts = query.order_by(Post.id.desc()).limit(limit).all()
    
    result = []
    for post in posts:
        author = post.persona
        author_name = "알 수 없음" if author.status == "DELETED" else f"{author.nickname}#{author.tag}"
        is_spoiler = post.is_spoiler == 1
        
        tags = db.query(Hashtag.normalized_keyword).join(PostHashtag, Hashtag.id == PostHashtag.hashtag_id).filter(PostHashtag.post_id == post.id).all()
        like_count = db.query(LikeLog).filter(LikeLog.target_type == "POST", LikeLog.target_id == post.id, LikeLog.is_active == 1).count()
        comment_count = db.query(Comment).filter(Comment.post_id == post.id, Comment.status == "ACTIVE").count()

        result.append({
            "id": post.id,
            "author_id": None if author.status == "DELETED" else author.id,
            "author": author_name,
            "author_image": None if author.status == "DELETED" else author.profile_image_url,
            "title": "*** 스포일러가 포함된 제목입니다 ***" if is_spoiler else post.title,
            "content": "*** 스포일러로 인해 블라인드 처리되었습니다. 보기 버튼을 눌러 확인하세요. ***" if is_spoiler else post.content,
            "image_urls": [] if is_spoiler else post.image_urls,
            "is_spoiler": is_spoiler,
            "created_at": post.created_at,
            "movies": [{"id": m.id, "title": m.title} for m in post.movies],
            "hashtags": [t[0] for t in tags],
            "like_count": like_count,
            "comment_count": comment_count
        })
    
    next_cursor = result[-1]["id"] if result else None
    return {"items": result, "next_cursor": next_cursor, "has_next": len(result) == limit}

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
    
    # 해시태그 목록 조회
    tags = db.query(Hashtag.normalized_keyword).join(
        PostHashtag, Hashtag.id == PostHashtag.hashtag_id
    ).filter(PostHashtag.post_id == post.id).all()
    hashtag_list = [t[0] for t in tags]
    
    # 통계 데이터 (좋아요, 댓글 수) 조회
    like_count = db.query(LikeLog).filter(
        LikeLog.target_type == "POST", LikeLog.target_id == post.id, LikeLog.is_active == 1
    ).count()
    comment_count = db.query(Comment).filter(
        Comment.post_id == post.id, Comment.status == "ACTIVE"
    ).count()

    return {
        "id": post.id, 
        "author_id": None if author.status == "DELETED" else author.id,
        "author": author_name, 
        "author_image": None if author.status == "DELETED" else author.profile_image_url,
        "title": post.title, 
        "content": post.content, 
        "image_urls": post.image_urls, 
        "is_spoiler": post.is_spoiler == 1,
        "movies": [{"id": m.id, "title": m.title} for m in post.movies],
        "hashtags": hashtag_list,
        "like_count": like_count,
        "comment_count": comment_count,
        "created_at": post.created_at
    }