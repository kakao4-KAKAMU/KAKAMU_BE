from fastapi import APIRouter

from . import live, for_you, user, content, custom_search

router = APIRouter()

# 각 탭 및 기능별 라우터를 통합
router.include_router(live.router)
router.include_router(for_you.router)
router.include_router(user.router)
router.include_router(content.router)
router.include_router(custom_search.router)