from fastapi import APIRouter
from app.api.endpoints import system, users, community, content, ai
from app.api.endpoints.movie_analyzer import movie_analyzer

api_router = APIRouter()

api_router.include_router(system.router)
api_router.include_router(users.router)
api_router.include_router(community.router)
api_router.include_router(content.router)
api_router.include_router(ai.router)
api_router.include_router(movie_analyzer.router)