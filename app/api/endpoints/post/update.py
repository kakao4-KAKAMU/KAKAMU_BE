from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from app.db.session import get_db
from app.api.deps import get_current_persona
from app.schemas.post.update import PostUpdate
from app.models import Post, PostMovie, Hashtag, PostHashtag, Persona, PostMention
from app.utils.parser import parse_content
from app.service.recommendation import recommendation_service
import re

router = APIRouter()

@router.put("/{post_id}")
async def update_post(
    post_id: int,
    post_in: PostUpdate,
    db: Session = Depends(get_db),
    persona_id: UUID = Depends(get_current_persona)
):
    """게시물을 수정합니다. 본문이 수정되면 '수정됨' 표시를 위한 갱신이 일어납니다."""
    post = db.query(Post).filter(Post.id == post_id, Post.status == "ACTIVE").first()
    if not post:
        raise HTTPException(status_code=404, detail="게시물을 찾을 수 없습니다.")
        
    if post.persona_id != persona_id:
        raise HTTPException(status_code=403, detail="본인이 작성한 게시물만 수정할 수 있습니다.")

    # 업데이트할 필드 적용
    if post_in.title is not None:
        post.title = post_in.title
    if post_in.content is not None:
        post.content = post_in.content
        # TODO: 추후 DB 마이그레이션 시 post.is_edited = True 플래그 적용 가능
        # 현재는 updated_at 시간 갱신 등으로 대체 가능
    if post_in.image_urls is not None:
        post.image_urls = post_in.image_urls
    if post_in.is_spoiler is not None:
        post.is_spoiler = post_in.is_spoiler

    # 영화 태그 수정 로직 (기존 태그 삭제 후 재등록 - Hard Delete or Inactive)
    if post_in.movie_ids is not None:
        # 1. 기존 태그 추천 가중치 롤백
        existing_movies = db.query(PostMovie).filter(PostMovie.post_id == post.id).all()
        for em in existing_movies:
            await recommendation_service.record_ml_relationship_log(
                db, persona_id, "MOVIE", em.movie_id, "create_post", base_score=2.0, is_undo=True
            )
            
        db.query(PostMovie).filter(PostMovie.post_id == post.id).delete()
        for m_id in post_in.movie_ids:
            db.add(PostMovie(post_id=post.id, movie_id=m_id))
            # 2. 새 태그 추천 가중치 반영
            await recommendation_service.record_ml_relationship_log(
                db, persona_id, "MOVIE", m_id, "create_post", base_score=2.0
            )
            
    # 본문(content)이 수정된 경우 해시태그/멘션도 다시 추출하여 연결
    if post_in.content is not None:
        db.query(PostHashtag).filter(PostHashtag.post_id == post.id).delete()
        db.query(PostMention).filter(PostMention.post_id == post.id).delete()
        
        hashtags, mentions = parse_content(post_in.content)
        
        normalized_set = set()
        for tag_keyword in hashtags:
            clean_keyword = re.sub(r'[^\w가-힣]', '', tag_keyword).lower()
            if clean_keyword:
                normalized_set.add(clean_keyword)
                
        for clean_keyword in list(normalized_set)[:10]: # 최대 10개 제한 적용
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
            target_persona = db.query(Persona).filter(Persona.nickname == nickname, Persona.tag == tag, Persona.status == "ACTIVE").first()
            if target_persona:
                db.add(PostMention(post_id=post.id, persona_id=target_persona.id))

    db.commit()
    return {"status": "success", "post_id": post.id}