from fastapi import APIRouter
from app.api.v1.endpoints import (
    GEM_pipeline, 
    auth, 
    dataset_metadata, 
    iggielgn_pipeline, 
    users, 
    shipping_lanes,
    routing,
    simple_routing,
    maritime_routes, 
    internetworkrouting
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(iggielgn_pipeline.router, prefix="/iggielgn", tags=["iggielgns"])
api_router.include_router(GEM_pipeline.router, prefix="/gem", tags=["gem"])
api_router.include_router(dataset_metadata.router, prefix="/datasets", tags=["dataset_metadata"])
api_router.include_router(shipping_lanes.router, prefix="/shipping-lanes", tags=["shipping_lanes"])
api_router.include_router(simple_routing.router, prefix="/routes", tags=["simple-routing"])
api_router.include_router(routing.router, prefix="/routing", tags=["routing"])
api_router.include_router(maritime_routes.router, prefix="/maritime-routes", tags=["maritime-routes"])
api_router.include_router(internetworkrouting.router, prefix="/internetwork-routing", tags=["internetwork-routing"])