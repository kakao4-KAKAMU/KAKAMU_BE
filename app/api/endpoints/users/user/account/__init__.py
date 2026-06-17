from fastapi import APIRouter
from . import auth_link, info, reset_password, restore, terminate, update, phone_verification

router = APIRouter()

router.include_router(auth_link.router)
router.include_router(info.router)
router.include_router(reset_password.router)
router.include_router(phone_verification.router)
router.include_router(restore.router)
router.include_router(terminate.router)
router.include_router(update.router)