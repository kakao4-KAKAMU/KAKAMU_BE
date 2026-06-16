from fastapi import APIRouter
from . import create_persona, read_persona, update_persona, delete_persona

router = APIRouter()

router.include_router(create_persona.router)
router.include_router(read_persona.router)
router.include_router(update_persona.router)
router.include_router(delete_persona.router)