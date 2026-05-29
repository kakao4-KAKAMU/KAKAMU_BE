from uuid import UUID
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models import Post, Hashtag, PostHashtag, Comment, LikeLog, Block

class PostReadService:
    def get_posts(self, db: Session, current_persona_id: UUID, cursor: Optional[int], limit: int) -> Dict[str, Any]:
        """게시물 피드 조회 로직"""
        blocked_by_me = db.query(Block.blocked_id).filter(Block.blocker_id == current_persona_id).all()
        blocking_me = db.query(Block.blocker_id).filter(Block.blocked_id == current_persona_id).all()
        excluded_persona_ids = [b[0] for b in blocked_by_me] + [b[0] for b in blocking_me]

        query = db.query(Post).filter(Post.status == "ACTIVE")
        
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
            
            tags = db.query(Hashtag.normalized_keyword).join(
                PostHashtag, Hashtag.id == PostHashtag.hashtag_id
            ).filter(PostHashtag.post_id == post.id).all()
            hashtag_list = [t[0] for t in tags]
            
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
                "movies": [{"id": m.id, "title": m.title} for m in post.movies],
                "hashtags": hashtag_list,
                "like_count": like_count,
                "comment_count": comment_count
            })
        
        next_cursor = result[-1]["id"] if result else None
        return {"items": result, "next_cursor": next_cursor, "has_next": len(result) == limit}

    def get_my_liked_posts(self, db: Session, current_persona_id: UUID, cursor: Optional[int], limit: int) -> Dict[str, Any]:
        """내가 좋아요 누른 게시물 조회 로직"""
        blocked_by_me = db.query(Block.blocked_id).filter(Block.blocker_id == current_persona_id).all()
        blocking_me = db.query(Block.blocker_id).filter(Block.blocked_id == current_persona_id).all()
        excluded_persona_ids = [b[0] for b in blocked_by_me] + [b[0] for b in blocking_me]

        liked_post_ids_subquery = db.query(LikeLog.target_id).filter(
            LikeLog.persona_id == current_persona_id,
            LikeLog.target_type == "POST",
            LikeLog.is_active == 1
        ).subquery()

        query = db.query(Post).filter(Post.id.in_(liked_post_ids_subquery), Post.status == "ACTIVE")
        
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
                "id": post.id, "author_id": None if author.status == "DELETED" else author.id, "author": author_name,
                "author_image": None if author.status == "DELETED" else author.profile_image_url,
                "title": "*** 스포일러가 포함된 제목입니다 ***" if is_spoiler else post.title,
                "content": "*** 스포일러로 인해 블라인드 처리되었습니다. 보기 버튼을 눌러 확인하세요. ***" if is_spoiler else post.content,
                "image_urls": [] if is_spoiler else post.image_urls, "is_spoiler": is_spoiler, "created_at": post.created_at,
                "movies": [{"id": m.id, "title": m.title} for m in post.movies], "hashtags": [t[0] for t in tags],
                "like_count": like_count, "comment_count": comment_count
            })
        
        next_cursor = result[-1]["id"] if result else None
        return {"items": result, "next_cursor": next_cursor, "has_next": len(result) == limit}

    def get_post_detail(self, db: Session, post_id: int) -> Dict[str, Any]:
        """게시물 상세 조회 로직"""
        post = db.query(Post).filter(Post.id == post_id, Post.status == "ACTIVE").first()
        if not post:
            raise HTTPException(status_code=404, detail={"code": "POST_NOT_FOUND", "message": "게시물을 찾을 수 없습니다."})
            
        author = post.persona
        author_name = "알 수 없음" if author.status == "DELETED" else f"{author.nickname}#{author.tag}"
        
        tags = db.query(Hashtag.normalized_keyword).join(PostHashtag, Hashtag.id == PostHashtag.hashtag_id).filter(PostHashtag.post_id == post.id).all()
        
        like_count = db.query(LikeLog).filter(LikeLog.target_type == "POST", LikeLog.target_id == post.id, LikeLog.is_active == 1).count()
        comment_count = db.query(Comment).filter(Comment.post_id == post.id, Comment.status == "ACTIVE").count()

        return {
            "id": post.id, "author_id": None if author.status == "DELETED" else author.id, "author": author_name,
            "author_image": None if author.status == "DELETED" else author.profile_image_url,
            "title": post.title, "content": post.content, "image_urls": post.image_urls, "is_spoiler": post.is_spoiler == 1,
            "movies": [{"id": m.id, "title": m.title} for m in post.movies], "hashtags": [t[0] for t in tags],
            "like_count": like_count, "comment_count": comment_count, "created_at": post.created_at
        }

post_read_service = PostReadService()