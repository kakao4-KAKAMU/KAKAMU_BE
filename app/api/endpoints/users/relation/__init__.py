from fastapi import APIRouter
from . import manage
router = APIRouter()

router.include_router(manage.router)
