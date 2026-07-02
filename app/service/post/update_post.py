from uuid import UUID
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models import Post, PostMovie, Hashtag, PostHashtag, User, PostMention
from app.utils.parser import parse_content
from app.service.post.ml_sync import post_ml_sync_service
from app.service.post.redis import post_cache_service
from app.schemas.request.post import PostUpdate

class PostUpdateService:
    async def update_post(self, db: Session, post_id: int, post_in: PostUpdate, user_id: UUID, persona_id: UUID) -> int:
        
        """게시물 수정 로직"""
        post = db.query(Post).filter(Post.id == post_id, Post.status == "ACTIVE").first()
        if not post:
            raise HTTPException(status_code=404, detail={"code": "POST_NOT_FOUND", "message": "게시물을 찾을 수 없습니다."})
            
        if post.user_id != user_id:
            raise HTTPException(status_code=403, detail={"code": "FORBIDDEN_POST_UPDATE", "message": "본인이 작성한 게시물만 수정할 수 있습니다."})

        # 1. 단순 필드(제목, 이미지, 스포일러)는 그대로 덮어쓰기
        post.title = post_in.title
        post.image_urls = post_in.image_urls
        post.is_spoiler = post_in.is_spoiler
        
        # post.persona_id = persona_id  # 💡 만약 수정 시 현재 페르소나로 작성자를 갱신하고 싶다면 주석 해제

        # 2. 영화 태그 수정 로직 (기존 데이터와 비교하여 변경된 부분만 ML 로그 및 DB 반영)
        
        existing_movies = db.query(PostMovie).filter(PostMovie.post_id == post.id).all()
        current_movie_ids = {em.movie_id for em in existing_movies}
        new_movie_ids = set(post_in.movie_ids)

        movies_to_remove = current_movie_ids - new_movie_ids
        movies_to_add = new_movie_ids - current_movie_ids

        # 원본 게시물을 작성했던 페르소나의 ML 데이터를 수정해야 하므로 원본 페르소나 ID 사용
        target_persona_id = post.persona_id or persona_id

        if movies_to_remove:
            db.query(PostMovie).filter(PostMovie.post_id == post.id, PostMovie.movie_id.in_(list(movies_to_remove))).delete(synchronize_session=False)

        if movies_to_add:
            for m_id in movies_to_add:
                db.add(PostMovie(post_id=post.id, movie_id=m_id))

        # 3. 본문(content)이 변경되었을 때만 해시태그/멘션 DB 삭제 및 재추출 로직 실행 (성능 최적화)
        if post.content != post_in.content:
            post.content = post_in.content
            db.query(PostHashtag).filter(PostHashtag.post_id == post.id).delete()
            db.query(PostMention).filter(PostMention.post_id == post.id).delete()
            
            hashtags, mentions = parse_content(post_in.content)
            
            if len(hashtags) > 10:
                raise HTTPException(status_code=400, detail={"code": "HASHTAG_LIMIT_EXCEEDED", "message": "해시태그는 최대 10개까지만 등록할 수 있습니다."})

            for clean_keyword in hashtags:
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
        post_cache_service.invalidate_post(post.id)

        await post_ml_sync_service.sync_update(
            db,
            post_id=post.id,
            user_id=user_id,
            persona_id=target_persona_id,
            post_in=post_in,
        )
        return post.id

post_update_service = PostUpdateService()