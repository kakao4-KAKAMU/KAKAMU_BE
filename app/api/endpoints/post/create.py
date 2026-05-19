from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import Any

from app.db.session import get_db
from app.api.deps import get_current_persona
from app.schemas.post import PostCreate
from app.models.models import Post, PostMovie, Hashtag, PostHashtag, Persona, PostMention
from app.utils.parser import parse_content

router = APIRouter()

@router.post("/", status_code=201)
def create_post(
    post_in: PostCreate,
    db: Session = Depends(get_db),
    persona_id: int = Depends(get_current_persona) # 현재 활성화된 페르소나 ID
) -> Any:
    """새로운 게시물을 작성하고 해시태그 및 멘션을 파싱하여 연결합니다."""
    try:
        new_post = Post(
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

        for tag_keyword in hashtags:
            hashtag_obj = db.query(Hashtag).filter(Hashtag.normalized_keyword == tag_keyword).first()
            if not hashtag_obj:
                hashtag_obj = Hashtag(normalized_keyword=tag_keyword)
                db.add(hashtag_obj)
                db.flush()
            db.add(PostHashtag(post_id=new_post.id, hashtag_id=hashtag_obj.id))

        for mention_str in mentions:
            nickname, tag = mention_str.split("#")
            
            target_persona = db.query(Persona).filter(
                Persona.nickname == nickname, Persona.tag == tag, Persona.status == "ACTIVE"
            ).first()
            if target_persona:
                db.add(PostMention(post_id=new_post.id, persona_id=target_persona.id))

        db.commit()
        return {"status": "success", "post_id": new_post.id}
    except IntegrityError as e:
        db.rollback()
        print(f"Create Post Integrity Error: {str(e)}")
        raise HTTPException(status_code=400, detail="잘못된 참조 데이터가 포함되어 있습니다. (예: 존재하지 않는 영화 ID)")
    except Exception as e:
        db.rollback()
        print(f"Create Post Error: {str(e)}")
        raise HTTPException(status_code=500, detail="게시물 작성 중 서버 오류가 발생했습니다.")

# --- 차후 백엔드에서 이미지를 직접 업로드 받아야 할 경우를 대비한 예시 코드 ---
# from fastapi import File, UploadFile
# from typing import List
#
# @router.post("/upload-images", status_code=201)
# async def upload_images_directly(
#     files: List[UploadFile] = File(...),
#     persona_id: int = Depends(get_current_persona)
# ) -> Any:
#     """
#     [참고용] 프론트엔드에서 클라우드로 직접 업로드(Direct Upload)하지 않고,
#     백엔드 서버를 거쳐서 이미지를 업로드해야 할 경우 사용하는 엔드포인트 예시입니다.
#     """
#     uploaded_urls = []
#     for file in files:
#         # 1. 파일 확장자 및 MIME 타입 유효성 검사 (Zero-Trust)
#         if file.content_type not in ["image/jpeg", "image/png", "image/gif"]:
#             raise HTTPException(status_code=400, detail="지원하지 않는 이미지 형식입니다.")
#             
#         # 2. 파일 저장 로직 (예: AWS S3, Google Cloud Storage, 또는 로컬 디스크)
#         # file_content = await file.read()
#         # url = await upload_to_storage(file_content, file.filename)
#         # uploaded_urls.append(url)
#         pass
#         
#     return {"status": "success", "urls": uploaded_urls}