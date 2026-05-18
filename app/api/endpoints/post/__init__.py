from fastapi import APIRouter
from . import create, post_comment, read, update, delete

router = APIRouter()

router.include_router(create.router)
router.include_router(read.router)
router.include_router(update.router)
router.include_router(delete.router)
router.include_router(comment.router, prefix="/{post_id}/comments")