from fastapi import APIRouter
from . import local, social, refresh

router = APIRouter()
router.include_router(local.router)
router.include_router(social.router)
router.include_router(refresh.router)