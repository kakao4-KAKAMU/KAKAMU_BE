from fastapi import APIRouter
from . import post, comment, like, notification

# Community 도메인 통합 라우터
router = APIRouter()

# 하위 라우터 연결
router.include_router(post.router, prefix="/posts", tags=["Posts"])
router.include_router(comment.router, prefix="/comments", tags=["Comments"])
router.include_router(like.router, prefix="/likes", tags=["Likes"])
router.include_router(notification.router, prefix="/notifications", tags=["Notifications"])