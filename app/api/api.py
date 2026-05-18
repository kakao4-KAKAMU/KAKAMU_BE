from fastapi import APIRouter
from app.api.endpoints import movie, system, test, post, user, comment, like

api_router = APIRouter()
api_router.include_router(system.router, tags=["System"])
api_router.include_router(user.router, prefix="/users", tags=["Users"])
api_router.include_router(movie.router, prefix="/movies", tags=["Movies"])
api_router.include_router(post.router, prefix="/posts", tags=["Posts"])
api_router.include_router(comment.router, prefix="/comments", tags=["Comments"])
api_router.include_router(like.router, prefix="/likes", tags=["Likes"])