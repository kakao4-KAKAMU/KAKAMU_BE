from fastapi import APIRouter
from app.api.endpoints import user, movie, system, test,profile

api_router = APIRouter()
api_router.include_router(system.router, tags=["System"])
api_router.include_router(user.router, prefix="/users", tags=["Users"])
api_router.include_router(movie.router, prefix="/movies", tags=["Movies"])
api_router.include_router(test.router, prefix="/test", tags=["Tests"])

api_router.include_router(profile.router, prefix="/profiles", tags=["profiles"])
