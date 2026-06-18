from fastapi import APIRouter
from . import notification

router = APIRouter()

router.include_router(notification.router)
