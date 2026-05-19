from fastapi import APIRouter
from . import create, read, comment, like

router = APIRouter()

router.include_router(create.router)
router.include_router(read.router)
router.include_router(comment.router)
router.include_router(like.router)