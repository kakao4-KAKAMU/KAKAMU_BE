from fastapi import APIRouter
from . import save

router = APIRouter()

router.include_router(save.router)
