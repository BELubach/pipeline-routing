
import json
from select import select

from fastapi import APIRouter, Depends, Depends, Query
from sqlalchemy import func, select
from app.db.session import get_db
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.maritime_routes import MaritimeRoute
from app.models.maritime_routes import MaritimeRoutes as MaritimeRouteModel
router = APIRouter()


@router.get("", response_model=list[MaritimeRoute])
async def list_datasets(
    db: AsyncSession = Depends(get_db),
    limit: int | None = Query(
        None, description="Limit number of records returned (default: all)"),
) -> list[MaritimeRoute]:

    statement = (
        select(
            MaritimeRouteModel,
            func.ST_AsGeoJSON(MaritimeRouteModel.geometry).label("geometry"),
        )
        .order_by(MaritimeRouteModel.id)
    )
    if limit:
        statement = statement.limit(limit)
        
    result = await db.execute(statement)
    rows = result.all()

    segments = [
        MaritimeRoute(
            geometry=json.loads(geometry) if geometry else None,
        )
        for _, geometry in rows
    ]

    return segments
