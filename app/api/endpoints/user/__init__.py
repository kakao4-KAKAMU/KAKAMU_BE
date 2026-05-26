from fastapi import APIRouter
from . import register, login, reset_password
# from . import profile

router = APIRouter()

router.include_router(register.router, prefix="/register")
router.include_router(login.router, prefix="/login")
router.include_router(reset_password.router)
# router.include_router(profile.router)