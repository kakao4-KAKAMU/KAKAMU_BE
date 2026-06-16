from fastapi import APIRouter
from . import register, login, account

router = APIRouter()

router.include_router(register.router, prefix="/register", tags=["Register"])
router.include_router(login.router, prefix="/login", tags=["Login"])
router.include_router(account.router, tags=["Account"])