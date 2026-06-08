from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Any
from uuid import UUID

from app.db.session import get_db
from app.api.deps import get_current_persona
from app.api.deps.auth import get_active_user
from app.models.user import User
from app.schemas.request.post import PostCreate
from app.schemas.response.common import PostIdResponse
from app.service.post.create_post import post_create_service

router = APIRouter()

@router.post("/", status_code=201, response_model=PostIdResponse)
async def create_post(
    post_in: PostCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_active_user),
    persona_id: UUID = Depends(get_current_persona) # 현재 활성화된 페르소나 ID (추천용)
) -> Any:
    """새로운 게시물을 작성하고 해시태그 및 멘션을 파싱하여 연결합니다."""
    post_id = await post_create_service.create_post(db, post_in, current_user.id, persona_id)
    return {"status": "success", "post_id": post_id}

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
#             raise HTTPException(status_code=400, detail={"code": "UNSUPPORTED_IMAGE_FORMAT", "message": "지원하지 않는 이미지 형식입니다."})
#             
#         # 2. 파일 저장 로직 (예: AWS S3, Google Cloud Storage, 또는 로컬 디스크)
#         # file_content = await file.read()
#         # url = await upload_to_storage(file_content, file.filename)
#         # uploaded_urls.append(url)
#         pass
#         
#     return {"status": "success", "urls": uploaded_urls}