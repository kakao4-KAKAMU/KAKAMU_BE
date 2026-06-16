from fastapi import APIRouter
from . import comment

router = APIRouter()

router.include_router(comment.router)
