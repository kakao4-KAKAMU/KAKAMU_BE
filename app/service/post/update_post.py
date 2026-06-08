import re
from uuid import UUID
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models import Post, PostMovie, Hashtag, PostHashtag, User, PostMention
from app.utils.parser import parse_content
from app.service.recommendation.recommendation_service import recommendation_service
from app.schemas.request.post import PostUpdate

class PostUpdateService:
    async def update_post(self, db: Session, post_id: int, post_in: PostUpdate, user_id: UUID, persona_id: UUID) -> int:
        """게시물 수정 로직"""
        post = db.query(Post).filter(Post.id == post_id, Post.status == "ACTIVE").first()
        if not post:
            raise HTTPException(status_code=404, detail={"code": "POST_NOT_FOUND", "message": "게시물을 찾을 수 없습니다."})
            
        if post.user_id != user_id:
            raise HTTPException(status_code=403, detail={"code": "FORBIDDEN_POST_UPDATE", "message": "본인이 작성한 게시물만 수정할 수 있습니다."})

        # 업데이트할 필드 적용
        if post_in.title is not None:
            post.title = post_in.title
        if post_in.content is not None:
            post.content = post_in.content
        if post_in.image_urls is not None:
            post.image_urls = post_in.image_urls
        if post_in.is_spoiler is not None:
            post.is_spoiler = post_in.is_spoiler

        # 영화 태그 수정 로직
        if post_in.movie_ids is not None:
            existing_movies = db.query(PostMovie).filter(PostMovie.post_id == post.id).all()
            for em in existing_movies:
                await recommendation_service.record_ml_relationship_log(
                    db, persona_id, "MOVIE", em.movie_id, "create_post", base_score=2.0, is_undo=True
                )
            db.query(PostMovie).filter(PostMovie.post_id == post.id).delete()
            for m_id in post_in.movie_ids:
                db.add(PostMovie(post_id=post.id, movie_id=m_id))
                await recommendation_service.record_ml_relationship_log(
                    db, persona_id, "MOVIE", m_id, "create_post", base_score=2.0
                )

        # 본문(content) 수정 시 해시태그/멘션 재추출
        if post_in.content is not None:
            db.query(PostHashtag).filter(PostHashtag.post_id == post.id).delete()
            db.query(PostMention).filter(PostMention.post_id == post.id).delete()
            
            hashtags, mentions = parse_content(post_in.content)
            
            if len(hashtags) > 10:
                raise HTTPException(status_code=400, detail={"code": "HASHTAG_LIMIT_EXCEEDED", "message": "해시태그는 최대 10개까지만 등록할 수 있습니다."})

            normalized_set = set()
            for tag_keyword in hashtags:
                clean_keyword = re.sub(r'[^\w가-힣]', '', tag_keyword).lower()
                if clean_keyword:
                    normalized_set.add(clean_keyword)
                    
            for clean_keyword in normalized_set:
                hashtag_obj = db.query(Hashtag).filter(Hashtag.normalized_keyword == clean_keyword).first()
                if not hashtag_obj:
                    hashtag_obj = Hashtag(normalized_keyword=clean_keyword)
                    db.add(hashtag_obj)
                    db.flush()
                db.add(PostHashtag(post_id=post.id, hashtag_id=hashtag_obj.id))

            for mention_str in mentions:
                if "#" not in mention_str:
                    continue
                nickname, tag = mention_str.split("#", 1)
                target_user = db.query(User).filter(
                    User.nickname == nickname, User.tag == tag, User.status == "ACTIVE"
                ).first()
                if target_user:
                    db.add(PostMention(post_id=post.id, user_id=target_user.id))

        db.commit()
        return post.id

post_update_service = PostUpdateService()