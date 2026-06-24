
import json
from select import select

from fastapi import APIRouter, Depends, Depends, Query
from sqlalchemy import func, select
from app.db.session import get_db
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.maritime_routes import MaritimeRouteSegment
from app.models.maritime_routes import MaritimeRoutes as MaritimeRouteModel
router = APIRouter()


@router.get("/segments", response_model=list[MaritimeRouteSegment])
async def list_datasets(
    db: AsyncSession = Depends(get_db),
    limit: int | None = Query(
        None, description="Limit number of records returned (default: all)"),
) -> list[MaritimeRouteSegment]:

    statement = (
        select(
            MaritimeRouteModel,
            MaritimeRouteModel.source,
            MaritimeRouteModel.target,
            func.ST_AsGeoJSON(MaritimeRouteModel.geometry).label("geometry"),
        )
       
    )
    if limit:
        statement = statement.limit(limit)
        
    result = await db.execute(statement)
    rows = result.all()
    print(rows)

    segments = [
        MaritimeRouteSegment(
            id=route.id,
            from_node=route.source,
            to_node=route.target,
            geometry=json.loads(geometry) if geometry else None,
        )
        for route, geometry in rows
    ]

    return segments
