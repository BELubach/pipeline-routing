from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.services.routing import get_internetwork_route
from app.schemas.routing import RouteRequest, RouteResponse, RouteStep

router = APIRouter()

@router.post("/route", response_model=RouteResponse)
async def get_route(request: RouteRequest, db: AsyncSession = Depends(get_db)):


    try:
        result = await get_internetwork_route(
            db,
            start_node_id=request.start.id,
            start_node_type=request.start.node_type,
            end_node_id=request.end.id,
            end_node_type=request.end.node_type,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    steps = [
        RouteStep(
            seq=s.seq,
            node_id=s.node_id,
            node_type=s.node_type,
            edge_id=s.edge_id,
            segment_km=s.segment_km,
            cumulative_km=s.cumulative_km,
            network=s.network,
        )
        for s in result.steps
    ]

    return RouteResponse(
        start    = request.start,
        end      = request.end,
        total_km = result.total_km,
        steps    = steps,
    )

