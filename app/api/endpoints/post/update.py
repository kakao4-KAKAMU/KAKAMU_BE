from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.api.deps import get_current_persona
from app.schemas.post.update import PostUpdate
from app.models.models import Post, PostMovie
from app.utils.parser import parse_content

router = APIRouter()

@router.put("/{post_id}")
def update_post(
    post_id: int,
    post_in: PostUpdate,
    db: Session = Depends(get_db),
    persona_id: int = Depends(get_current_persona)
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
        db.query(PostMovie).filter(PostMovie.post_id == post.id).delete()
        for m_id in post_in.movie_ids:
            db.add(PostMovie(post_id=post.id, movie_id=m_id))
            
    # 참고: 본문(content)이 수정된 경우 해시태그/멘션도 다시 추출하여 연결하는 로직이 추가로 필요합니다.
    # if post_in.content is not None:
    #     hashtags, mentions = parse_content(post_in.content)
    #     # 기존 연결 삭제 후 재연결 로직 추가...

    db.commit()
    return {"status": "success", "post_id": post.id}