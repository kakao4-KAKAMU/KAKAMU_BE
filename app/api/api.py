from fastapi import APIRouter
from app.api.endpoints import user, movie, system, test, post, comment, like

api_router = APIRouter()
api_router.include_router(system.router, tags=["System"])
api_router.include_router(user.router, prefix="/users", tags=["Users"])
api_router.include_router(movie.router, prefix="/movies", tags=["Movies"])
api_router.include_router(post.router, prefix="/posts", tags=["Posts"])