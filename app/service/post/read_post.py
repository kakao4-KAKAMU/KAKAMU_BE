from uuid import UUID
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException

from app.models import Post, Hashtag, PostHashtag, Comment, LikeLog, Block, Persona, PostMention

class PostReadService:
    def _get_mentions_for_posts(self, db: Session, post_ids: List[int]) -> Dict[int, List[Dict[str, Any]]]:
        if not post_ids:
            return {}
        
        mentions_query = db.query(PostMention.post_id, Persona.id, Persona.nickname, Persona.tag)\
            .join(Persona, Persona.id == PostMention.persona_id)\
            .filter(PostMention.post_id.in_(post_ids), Persona.status == "ACTIVE").all()
            
        mentions_map = {pid: [] for pid in post_ids}
        for m in mentions_query:
            mentions_map[m.post_id].append({
                "id": m.id,
                "nickname": m.nickname,
                "tag": m.tag
            })
        return mentions_map

    def _get_hashtags_for_posts(self, db: Session, post_ids: List[int]) -> Dict[int, List[str]]:
        if not post_ids:
            return {}
            
        hashtags_query = db.query(PostHashtag.post_id, Hashtag.normalized_keyword)\
            .join(Hashtag, Hashtag.id == PostHashtag.hashtag_id)\
            .filter(PostHashtag.post_id.in_(post_ids)).all()
            
        hashtags_map = {pid: [] for pid in post_ids}
        for h in hashtags_query:
            hashtags_map[h.post_id].append(h.normalized_keyword)
        return hashtags_map

    def _get_comment_counts_for_posts(self, db: Session, post_ids: List[int]) -> Dict[int, int]:
        if not post_ids:
            return {}
            
        counts = db.query(Comment.post_id, func.count(Comment.id))\
            .filter(Comment.post_id.in_(post_ids), Comment.status == "ACTIVE")\
            .group_by(Comment.post_id).all()
            
        return {pid: count for pid, count in counts}

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
        
        post_ids = [post.id for post in posts]
        liked_post_ids = set()
        mentions_map = {}
        hashtags_map = {}
        comment_counts_map = {}
        
        if post_ids:
            liked_logs = db.query(LikeLog.target_id).filter(
                LikeLog.persona_id == current_persona_id,
                LikeLog.target_type == "POST",
                LikeLog.target_id.in_(post_ids),
                LikeLog.is_active == 1
            ).all()
            liked_post_ids = {log[0] for log in liked_logs}
            
            mentions_map = self._get_mentions_for_posts(db, post_ids)
            hashtags_map = self._get_hashtags_for_posts(db, post_ids)
            comment_counts_map = self._get_comment_counts_for_posts(db, post_ids)
            
        result = []
        for post in posts:
            author = post.persona
            author_name = "알 수 없음" if author.status == "DELETED" else f"{author.nickname}#{author.tag}"
            is_spoiler = post.is_spoiler == 1

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
                "updated_at": post.updated_at,
                "movies": [{"id": m.id, "title": m.title} for m in post.movies],
                "hashtags": hashtags_map.get(post.id, []),
                "mentions": mentions_map.get(post.id, []),
                "like_count": post.like_count, # Use the model field instead of querying LikeLog
                "comment_count": comment_counts_map.get(post.id, 0),
                "is_liked": post.id in liked_post_ids
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
        
        post_ids = [post.id for post in posts]
        mentions_map = {}
        hashtags_map = {}
        comment_counts_map = {}
        
        if post_ids:
            mentions_map = self._get_mentions_for_posts(db, post_ids)
            hashtags_map = self._get_hashtags_for_posts(db, post_ids)
            comment_counts_map = self._get_comment_counts_for_posts(db, post_ids)

        result = []
        for post in posts:
            author = post.persona
            author_name = "알 수 없음" if author.status == "DELETED" else f"{author.nickname}#{author.tag}"
            is_spoiler = post.is_spoiler == 1

            result.append({
                "id": post.id, "author_id": None if author.status == "DELETED" else author.id, "author": author_name,
                "author_image": None if author.status == "DELETED" else author.profile_image_url,
                "title": "*** 스포일러가 포함된 제목입니다 ***" if is_spoiler else post.title,
                "content": "*** 스포일러로 인해 블라인드 처리되었습니다. 보기 버튼을 눌러 확인하세요. ***" if is_spoiler else post.content,
                "image_urls": [] if is_spoiler else post.image_urls, "is_spoiler": is_spoiler, 
                "created_at": post.created_at, "updated_at": post.updated_at,
                "movies": [{"id": m.id, "title": m.title} for m in post.movies], 
                "hashtags": hashtags_map.get(post.id, []),
                "mentions": mentions_map.get(post.id, []),
                "like_count": post.like_count, # Use the model field
                "comment_count": comment_counts_map.get(post.id, 0),
                "is_liked": True
            })
        
        next_cursor = result[-1]["id"] if result else None
        return {"items": result, "next_cursor": next_cursor, "has_next": len(result) == limit}

    def get_persona_posts(self, db: Session, target_persona_id: UUID, current_persona_id: UUID, cursor: Optional[int], limit: int) -> Dict[str, Any]:
        """특정 페르소나가 작성한 게시물 조회 로직"""
        blocked_by_me = db.query(Block.blocked_id).filter(Block.blocker_id == current_persona_id).all()
        blocking_me = db.query(Block.blocker_id).filter(Block.blocked_id == current_persona_id).all()
        excluded_persona_ids = [b[0] for b in blocked_by_me] + [b[0] for b in blocking_me]

        # 차단 관계일 경우 빈 목록 반환 (프로필 주인이 나와 차단 관계라면 글을 볼 수 없음)
        if target_persona_id in excluded_persona_ids:
            return {"items": [], "next_cursor": None, "has_next": False}

        query = db.query(Post).filter(Post.persona_id == target_persona_id, Post.status == "ACTIVE")
        
        if cursor:
            query = query.filter(Post.id < cursor)
        
        posts = query.order_by(Post.id.desc()).limit(limit).all()
        
        post_ids = [post.id for post in posts]
        liked_post_ids = set()
        mentions_map = {}
        hashtags_map = {}
        comment_counts_map = {}
        
        if post_ids:
            liked_logs = db.query(LikeLog.target_id).filter(
                LikeLog.persona_id == current_persona_id,
                LikeLog.target_type == "POST",
                LikeLog.target_id.in_(post_ids),
                LikeLog.is_active == 1
            ).all()
            liked_post_ids = {log[0] for log in liked_logs}
            
            mentions_map = self._get_mentions_for_posts(db, post_ids)
            hashtags_map = self._get_hashtags_for_posts(db, post_ids)
            comment_counts_map = self._get_comment_counts_for_posts(db, post_ids)

        result = []
        for post in posts:
            author = post.persona
            author_name = "알 수 없음" if author.status == "DELETED" else f"{author.nickname}#{author.tag}"
            is_spoiler = post.is_spoiler == 1

            result.append({
                "id": post.id, "author_id": None if author.status == "DELETED" else author.id, "author": author_name,
                "author_image": None if author.status == "DELETED" else author.profile_image_url,
                "title": "*** 스포일러가 포함된 제목입니다 ***" if is_spoiler else post.title,
                "content": "*** 스포일러로 인해 블라인드 처리되었습니다. 보기 버튼을 눌러 확인하세요. ***" if is_spoiler else post.content,
                "image_urls": [] if is_spoiler else post.image_urls, "is_spoiler": is_spoiler, 
                "created_at": post.created_at, "updated_at": post.updated_at,
                "movies": [{"id": m.id, "title": m.title} for m in post.movies], 
                "hashtags": hashtags_map.get(post.id, []),
                "mentions": mentions_map.get(post.id, []),
                "like_count": post.like_count, 
                "comment_count": comment_counts_map.get(post.id, 0),
                "is_liked": post.id in liked_post_ids
            })
        
        next_cursor = result[-1]["id"] if result else None
        return {"items": result, "next_cursor": next_cursor, "has_next": len(result) == limit}

    def get_post_detail(self, db: Session, post_id: int, current_persona_id: UUID) -> Dict[str, Any]:
        """게시물 상세 조회 로직"""
        post = db.query(Post).filter(Post.id == post_id, Post.status == "ACTIVE").first()
        if not post:
            raise HTTPException(status_code=404, detail={"code": "POST_NOT_FOUND", "message": "게시물을 찾을 수 없습니다."})
            
        author = post.persona
        author_name = "알 수 없음" if author.status == "DELETED" else f"{author.nickname}#{author.tag}"
        
        hashtags_map = self._get_hashtags_for_posts(db, [post.id])
        mentions_map = self._get_mentions_for_posts(db, [post.id])
        comment_counts_map = self._get_comment_counts_for_posts(db, [post.id])
        
        is_liked = db.query(LikeLog).filter(
            LikeLog.persona_id == current_persona_id,
            LikeLog.target_type == "POST",
            LikeLog.target_id == post.id,
            LikeLog.is_active == 1
        ).first() is not None

        return {
            "id": post.id, "author_id": None if author.status == "DELETED" else author.id, "author": author_name,
            "author_image": None if author.status == "DELETED" else author.profile_image_url,
            "title": post.title, "content": post.content, "image_urls": post.image_urls, "is_spoiler": post.is_spoiler == 1,
            "movies": [{"id": m.id, "title": m.title} for m in post.movies], 
            "hashtags": hashtags_map.get(post.id, []),
            "mentions": mentions_map.get(post.id, []),
            "like_count": post.like_count, # Use the model field
            "comment_count": comment_counts_map.get(post.id, 0),
            "created_at": post.created_at, "updated_at": post.updated_at,
            "is_liked": is_liked
        }

post_read_service = PostReadService()