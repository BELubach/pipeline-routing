from fastapi import APIRouter
from app.api.v1.endpoints import auth, users, plants, pipelines

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(plants.router, prefix="/plants", tags=["plants"])
api_router.include_router(pipelines.router, prefix="/pipelines", tags=["pipelines"])
