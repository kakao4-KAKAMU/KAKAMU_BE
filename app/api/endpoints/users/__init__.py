from fastapi import APIRouter

from . import user, profile, relation

# Users 도메인 통합 라우터 (수정됨)
router = APIRouter()

# 하위 라우터 연결
router.include_router(user.router, prefix="/users")
router.include_router(profile.router, tags=["Personas"])
router.include_router(relation.router, prefix="/relations", tags=["Relations"])