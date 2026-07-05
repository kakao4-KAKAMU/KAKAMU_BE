from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException

from app.models import Post, PostMovie, Hashtag, PostHashtag, User, PostMention, UserStatus
from app.utils.parser import parse_content
from app.service.post.ml_sync import post_ml_sync_service
from app.service.post.post_agg_refresh import post_agg_refresh_service
from app.service.post.redis import post_cache_service
from app.schemas.request.post import PostCreate

class PostCreateService:
    async def create_post(self, db: Session, post_in: PostCreate, user_id: UUID, persona_id: UUID) -> int:
        """게시물 생성 및 해시태그/멘션 연동 로직"""
        try:
            new_post = Post(
                user_id=user_id,
                persona_id=persona_id,
                title=post_in.title,
                content=post_in.content,
                image_urls=post_in.image_urls,
                is_spoiler=post_in.is_spoiler
            )
            db.add(new_post)
            db.flush()

            for m_id in post_in.movie_ids:
                db.add(PostMovie(post_id=new_post.id, movie_id=m_id))

            hashtags, mentions = parse_content(post_in.content)

            if len(hashtags) > 10:
                raise HTTPException(status_code=400, detail={"code": "HASHTAG_LIMIT_EXCEEDED", "message": "해시태그는 최대 10개까지만 등록할 수 있습니다."})

            for clean_keyword in hashtags:
                hashtag_obj = db.query(Hashtag).filter(Hashtag.normalized_keyword == clean_keyword).first()
                if not hashtag_obj:
                    hashtag_obj = Hashtag(normalized_keyword=clean_keyword)
                    db.add(hashtag_obj)
                    db.flush()
                db.add(PostHashtag(post_id=new_post.id, hashtag_id=hashtag_obj.id))

            for mention_str in mentions:
                if "#" not in mention_str:
                    continue
                nickname, tag = mention_str.split("#", 1)
                target_user = db.query(User).filter(
                    User.nickname == nickname, User.tag == tag, User.status == UserStatus.ACTIVE
                ).first()
                if target_user:
                    db.add(PostMention(post_id=new_post.id, user_id=target_user.id))

            post_agg_refresh_service.refresh_post(db, new_post.id)
            db.commit()
            post_cache_service._populate_post_info_from_db(db, new_post.id)

            await post_ml_sync_service.sync_create(
                db,
                post_id=new_post.id,
                user_id=user_id,
                persona_id=persona_id,
                post_in=post_in,
            )

            return new_post.id

        except IntegrityError:
            db.rollback()
            raise HTTPException(status_code=400, detail={"code": "INVALID_REFERENCE_DATA", "message": "잘못된 참조 데이터가 포함되어 있습니다. (예: 존재하지 않는 영화 ID)"})
        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            print(e)
            raise HTTPException(status_code=500, detail={"code": "POST_CREATION_FAILED", "message": "게시물 작성 중 서버 오류가 발생했습니다."})

post_create_service = PostCreateService()
