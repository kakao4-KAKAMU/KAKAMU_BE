from fastapi import APIRouter
from . import health, log, test

# System 도메인 통합 라우터
router = APIRouter()

router.include_router(health.router, tags=["System"])
router.include_router(log.router, prefix="/logs", tags=["Logging"])
router.include_router(test.router, prefix="/test", tags=["Tests"])