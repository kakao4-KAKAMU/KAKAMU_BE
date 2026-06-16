from fastapi import APIRouter
from . import like

router = APIRouter()

router.include_router(like.router)
