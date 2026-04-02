from fastapi import APIRouter
from app.api.v1.endpoints import GEM_pipeline, auth, dataset_metadata, iggielgn_pipeline, users 

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(iggielgn_pipeline.router, prefix="/iggielgn", tags=["iggielgns"])
api_router.include_router(GEM_pipeline.router, prefix="/gem", tags=["gem"])
api_router.include_router(dataset_metadata.router, prefix="/dataset", tags=["dataset_metadata"])
