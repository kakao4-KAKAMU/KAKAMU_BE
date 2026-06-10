from fastapi import APIRouter
from . import movie, search

# Content 도메인 통합 라우터
router = APIRouter()

router.include_router(movie.router, prefix="/movies", tags=["Movies"])
router.include_router(search.router, tags=["Search"])