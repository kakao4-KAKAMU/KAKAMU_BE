from fastapi import APIRouter
from . import health, log, batch

# System 도메인 통합 라우터
router = APIRouter()

router.include_router(health.router, tags=["System"])
router.include_router(log.router, prefix="/logs", tags=["Logging"])
router.include_router(batch.router)