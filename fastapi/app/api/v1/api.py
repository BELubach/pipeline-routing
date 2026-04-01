from fastapi import APIRouter
from app.api.v1.endpoints import auth, iggielgn, users, dataset_metadata 

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(iggielgn.router, prefix="/iggielgn", tags=["iggielgns"])
api_router.include_router(dataset_metadata.router, prefix="/dataset", tags=["dataset_metadata"])
