from fastapi import APIRouter
from . import local, social

router = APIRouter()
router.include_router(local.router)
router.include_router(social.router)