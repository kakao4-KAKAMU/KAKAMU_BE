from fastapi import APIRouter
from app.api.endpoints import system, users, community, content, ai

api_router = APIRouter()

api_router.include_router(system.router)
api_router.include_router(users.router)
api_router.include_router(community.router)
api_router.include_router(content.router)
api_router.include_router(ai.router)