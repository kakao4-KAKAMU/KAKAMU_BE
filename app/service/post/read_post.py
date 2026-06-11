import time
from uuid import UUID
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import func, select
from fastapi import HTTPException

from app.models import Post, Hashtag, PostHashtag, Comment, LikeLog, Block, User, PostMention, Follow, Persona, Movie

class PostReadService:
    def __init__(self):
        # 차단 유저 인메모리 캐시 (Key: current_user_id, Value: (timestamp, {blocked_user_ids}))
        self._block_cache = {}
        self._cache_ttl = 60  # 캐시 유지 시간 (60초)

    def _get_cached_blocked_user_ids(self, db: Session, user_id: UUID) -> set:
        now = time.time()
        
        # 메모리 누수 방지: 캐시된 유저가 10,000명을 넘어가면 캐시 초기화
        if len(self._block_cache) > 10000:
            self._block_cache.clear()
            
        if user_id in self._block_cache:
            cached_time, block_set = self._block_cache[user_id]
            if now - cached_time < self._cache_ttl:
                return block_set
                
        blocked_by_me = db.query(Block.blocked_id).filter(Block.blocker_id == user_id).all()
        blocking_me = db.query(Block.blocker_id).filter(Block.blocked_id == user_id).all()
        
        block_set = {b[0] for b in blocked_by_me} | {b[0] for b in blocking_me}
        self._block_cache[user_id] = (now, block_set)
        return block_set

    def _get_mentions_for_posts(self, db: Session, post_ids: List[int]) -> Dict[int, List[Dict[str, Any]]]:
        if not post_ids:
            return {}
        
        mentions_query = db.query(PostMention.post_id, User.id, User.nickname)\
            .join(User, User.id == PostMention.user_id)\
            .filter(PostMention.post_id.in_(post_ids), User.status == "ACTIVE").all()
            
        mentions_map = {pid: [] for pid in post_ids}
        for m in mentions_query:
            mentions_map[m.post_id].append({
                "id": m.id,
                "nickname": m.nickname,
                "tag": m.tag # User로 통합된 태그 사용
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

    def _get_followed_user_ids(self, db: Session, current_user_id: UUID, target_user_ids: List[UUID]) -> set:
        if not target_user_ids:
            return set()
        follows = db.query(Follow.following_id).filter(
            Follow.follower_id == current_user_id,
            Follow.following_id.in_(target_user_ids)
        ).all()
        return {f[0] for f in follows}

    def get_posts(self, db: Session, current_user_id: UUID, cursor: Optional[int], limit: int) -> Dict[str, Any]:
        """게시물 피드 조회 로직"""
        # 1. 차단 유저 목록 캐시에서 가져오기
        blocked_user_ids = self._get_cached_blocked_user_ids(db, current_user_id)

        # 2. 게시물과 작성자(User) 조인 및 필터링 적용
        query = db.query(Post, User).join(User, Post.user_id == User.id).filter(
            Post.status == "ACTIVE",
            User.status == "ACTIVE"                # 탈퇴/삭제 유예 기간인 작성자 숨김
        ).options(selectinload(Post.movies).selectinload(Movie.titles))

        if blocked_user_ids:
            query = query.filter(Post.user_id.notin_(blocked_user_ids))

        if cursor:
            query = query.filter(Post.id < cursor)
        
        posts_with_author = query.order_by(Post.id.desc()).limit(limit).all()
        
        post_ids = [post.id for post, author in posts_with_author]
        liked_post_ids = set()
        followed_user_ids = set()
        mentions_map = {}
        hashtags_map = {}
        comment_counts_map = {}
        
        if post_ids:
            liked_logs = db.query(LikeLog.target_id).filter(
                LikeLog.user_id == current_user_id, # 좋아요는 user_id 기준 공유
                LikeLog.target_type == "POST",
                LikeLog.target_id.in_(post_ids),
                LikeLog.is_active == 1
            ).all()
            liked_post_ids = {log[0] for log in liked_logs}
            
            author_user_ids = list({post.user_id for post, author in posts_with_author})
            followed_user_ids = self._get_followed_user_ids(db, current_user_id, author_user_ids)
            
            mentions_map = self._get_mentions_for_posts(db, post_ids)
            hashtags_map = self._get_hashtags_for_posts(db, post_ids)
            comment_counts_map = self._get_comment_counts_for_posts(db, post_ids)
            
        result = []
        for post, author in posts_with_author:
            is_deleted = not author or author.status == "DELETED"
            author_name = "알 수 없음" if is_deleted else f"{author.nickname}#{author.tag}"
            is_spoiler = post.is_spoiler == 1

            result.append({
                "id": post.id,
                "author_id": None if is_deleted else author.id,
                "author": author_name,
                "author_nickname": "알 수 없음" if is_deleted else author.nickname,
                "author_tag": None if is_deleted else author.tag,
                "author_image": None if is_deleted else author.profile_image_url,
                "title": post.title,
                "content": post.content,
                "image_urls": post.image_urls,
                "is_spoiler": is_spoiler,
                "created_at": post.created_at,
                "updated_at": post.updated_at,
                "movies": [{"id": m.id, "title": m.titles[0].title_name if m.titles else "제목 없음"} for m in post.movies],
                "hashtags": hashtags_map.get(post.id, []),
                "mentions": mentions_map.get(post.id, []),
                "like_count": post.like_count, # Use the model field instead of querying LikeLog
                "comment_count": comment_counts_map.get(post.id, 0),
                "is_liked": post.id in liked_post_ids,
                "is_following": post.user_id in followed_user_ids if not is_deleted else False
            })
        
        next_cursor = result[-1]["id"] if result else None
        return {"items": result, "next_cursor": next_cursor, "has_next": len(result) == limit}

    def get_my_liked_posts(self, db: Session, current_user_id: UUID, cursor: Optional[int], limit: int) -> Dict[str, Any]:
        """내가 좋아요 누른 게시물 조회 로직"""
        # 1. 차단 유저 목록 캐시에서 가져오기
        blocked_user_ids = self._get_cached_blocked_user_ids(db, current_user_id)

        # 2. 내가 좋아요한 게시물 ID 서브쿼리
        liked_post_ids_subquery = select(LikeLog.target_id).where(
            LikeLog.user_id == current_user_id,
            LikeLog.target_type == "POST",
            LikeLog.is_active == 1
        )

        # 3. 조인 및 필터 적용
        query = db.query(Post, User).join(User, Post.user_id == User.id).filter(
            Post.id.in_(liked_post_ids_subquery), 
            Post.status == "ACTIVE",
            User.status == "ACTIVE"
        ).options(selectinload(Post.movies).selectinload(Movie.titles))
        
        if blocked_user_ids:
            query = query.filter(Post.user_id.notin_(blocked_user_ids))

        if cursor:
            query = query.filter(Post.id < cursor)
        
        posts_with_author = query.order_by(Post.id.desc()).limit(limit).all()
        
        post_ids = [post.id for post, author in posts_with_author]
        followed_user_ids = set()
        mentions_map = {}
        hashtags_map = {}
        comment_counts_map = {}
        
        if post_ids:
            author_user_ids = list({post.user_id for post, author in posts_with_author})
            followed_user_ids = self._get_followed_user_ids(db, current_user_id, author_user_ids)

            mentions_map = self._get_mentions_for_posts(db, post_ids)
            hashtags_map = self._get_hashtags_for_posts(db, post_ids)
            comment_counts_map = self._get_comment_counts_for_posts(db, post_ids)

        result = []
        for post, author in posts_with_author:
            is_deleted = not author or author.status == "DELETED"
            author_name = "알 수 없음" if is_deleted else f"{author.nickname}#{author.tag}"
            is_spoiler = post.is_spoiler == 1

            result.append({
                "id": post.id, 
                "author_id": None if is_deleted else author.id, 
                "author": author_name,
                "author_nickname": "알 수 없음" if is_deleted else author.nickname,
                "author_tag": None if is_deleted else author.tag,
                "author_image": None if is_deleted else author.profile_image_url,
                "title": post.title,
                "content": post.content,
                "image_urls": post.image_urls, "is_spoiler": is_spoiler, 
                "created_at": post.created_at, "updated_at": post.updated_at,
                "movies": [{"id": m.id, "title": m.titles[0].title_name if m.titles else "제목 없음"} for m in post.movies], 
                "hashtags": hashtags_map.get(post.id, []),
                "mentions": mentions_map.get(post.id, []),
                "like_count": post.like_count, # Use the model field
                "comment_count": comment_counts_map.get(post.id, 0),
                "is_liked": True,
                "is_following": post.user_id in followed_user_ids if not is_deleted else False
            })
        
        next_cursor = result[-1]["id"] if result else None
        return {"items": result, "next_cursor": next_cursor, "has_next": len(result) == limit}

    def get_user_posts(self, db: Session, target_persona_id: UUID, current_persona_id: UUID, current_user_id: UUID, cursor: Optional[int], limit: int) -> Dict[str, Any]:
        """특정 페르소나가 작성한 게시물 조회 로직"""
        target_user_id = db.scalar(select(Persona.user_id).where(Persona.id == target_persona_id))
        if not target_user_id:
            raise HTTPException(status_code=404, detail={"code": "PERSONA_NOT_FOUND", "message": "대상을 찾을 수 없습니다."})

        # 프로필 주인이 나와 차단 관계인지 캐시에서 확인 (user_id 기준)
        blocked_user_ids = self._get_cached_blocked_user_ids(db, current_user_id)
        if target_user_id in blocked_user_ids:
            return {"items": [], "next_cursor": None, "has_next": False}

        query = db.query(Post, User).join(User, Post.user_id == User.id).filter(
            Post.user_id == target_user_id, 
            Post.status == "ACTIVE",
            User.status == "ACTIVE"
        ).options(selectinload(Post.movies).selectinload(Movie.titles))
        
        if cursor:
            query = query.filter(Post.id < cursor)
        
        posts_with_author = query.order_by(Post.id.desc()).limit(limit).all()
        
        post_ids = [post.id for post, author in posts_with_author]
        liked_post_ids = set()
        followed_user_ids = set()
        mentions_map = {}
        hashtags_map = {}
        comment_counts_map = {}
        
        if post_ids:
            liked_logs = db.query(LikeLog.target_id).filter(
                LikeLog.user_id == current_user_id,
                LikeLog.target_type == "POST",
                LikeLog.target_id.in_(post_ids),
                LikeLog.is_active == 1
            ).all()
            liked_post_ids = {log[0] for log in liked_logs}
            
            author_user_ids = list({post.user_id for post, author in posts_with_author})
            followed_user_ids = self._get_followed_user_ids(db, current_user_id, author_user_ids)
            
            mentions_map = self._get_mentions_for_posts(db, post_ids)
            hashtags_map = self._get_hashtags_for_posts(db, post_ids)
            comment_counts_map = self._get_comment_counts_for_posts(db, post_ids)

        result = []
        for post, author in posts_with_author:
            is_deleted = not author or author.status == "DELETED"
            author_name = "알 수 없음" if is_deleted else f"{author.nickname}#{author.tag}"
            is_spoiler = post.is_spoiler == 1

            result.append({
                "id": post.id, 
                "author_id": None if is_deleted else author.id, 
                "author": author_name,
                "author_nickname": "알 수 없음" if is_deleted else author.nickname,
                "author_tag": None if is_deleted else author.tag,
                "author_image": None if is_deleted else author.profile_image_url,
                "title": post.title,
                "content": post.content,
                "image_urls": post.image_urls, "is_spoiler": is_spoiler, 
                "created_at": post.created_at, "updated_at": post.updated_at,
                "movies": [{"id": m.id, "title": m.titles[0].title_name if m.titles else "제목 없음"} for m in post.movies], 
                "hashtags": hashtags_map.get(post.id, []),
                "mentions": mentions_map.get(post.id, []),
                "like_count": post.like_count, 
                "comment_count": comment_counts_map.get(post.id, 0),
                "is_liked": post.id in liked_post_ids,
                "is_following": post.user_id in followed_user_ids if not is_deleted else False
            })
        
        next_cursor = result[-1]["id"] if result else None
        return {"items": result, "next_cursor": next_cursor, "has_next": len(result) == limit}

    def get_post_detail(self, db: Session, post_id: int, current_persona_id: UUID, current_user_id: UUID) -> Dict[str, Any]:
        """게시물 상세 조회 로직"""
        db_result = db.query(Post, User).join(User, Post.user_id == User.id)\
            .options(selectinload(Post.movies).selectinload(Movie.titles))\
            .filter(Post.id == post_id, Post.status == "ACTIVE").first()
            
        if not db_result:
            raise HTTPException(status_code=404, detail={"code": "POST_NOT_FOUND", "message": "게시물을 찾을 수 없습니다."})
            
        post, author = db_result
        # 차단 관계인지 캐시에서 확인
        blocked_user_ids = self._get_cached_blocked_user_ids(db, current_user_id)
        if post.user_id in blocked_user_ids:
            raise HTTPException(status_code=403, detail={"code": "FORBIDDEN_BLOCKED_POST", "message": "차단된 사용자의 게시물입니다."})

        is_deleted = not author or author.status == "DELETED"
        author_name = "알 수 없음" if is_deleted else f"{author.nickname}#{author.tag}"
        
        hashtags_map = self._get_hashtags_for_posts(db, [post.id])
        mentions_map = self._get_mentions_for_posts(db, [post.id])
        comment_counts_map = self._get_comment_counts_for_posts(db, [post.id])
        
        is_liked = db.query(LikeLog).filter(
            LikeLog.user_id == current_user_id,
            LikeLog.target_type == "POST",
            LikeLog.target_id == post.id,
            LikeLog.is_active == 1
        ).first() is not None

        is_following = False
        if not is_deleted:
            is_following = db.query(Follow).filter(
                Follow.follower_id == current_user_id,
                Follow.following_id == post.user_id
            ).first() is not None

        return {
            "id": post.id, 
            "author_id": None if is_deleted else author.id, 
            "author": author_name,
            "author_nickname": "알 수 없음" if is_deleted else author.nickname,
            "author_tag": None if is_deleted else author.tag,
            "author_image": None if is_deleted else author.profile_image_url,
            "title": post.title, "content": post.content, "image_urls": post.image_urls, "is_spoiler": post.is_spoiler == 1,
            "movies": [{"id": m.id, "title": m.titles[0].title_name if m.titles else "제목 없음"} for m in post.movies], 
            "hashtags": hashtags_map.get(post.id, []),
            "mentions": mentions_map.get(post.id, []),
            "like_count": post.like_count, # Use the model field
            "comment_count": comment_counts_map.get(post.id, 0),
            "created_at": post.created_at, "updated_at": post.updated_at,
            "is_liked": is_liked,
            "is_following": is_following
        }

post_read_service = PostReadService()