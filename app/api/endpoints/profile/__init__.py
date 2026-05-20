from fastapi import APIRouter

from .create_persona import router as new_router
from .update_persona import router as edit_router
from .delete_persona import router as delete_router

router = APIRouter()

router.include_router(new_router)
router.include_router(edit_router)
router.include_router(delete_router)