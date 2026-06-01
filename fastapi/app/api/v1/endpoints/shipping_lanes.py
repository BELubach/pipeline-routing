
import json
from select import select
from unittest import result

from fastapi import APIRouter, Depends, Depends, Query
from app.models.shipping_lanes import ShippingLane
from sqlalchemy import func, select
from app.schemas.shipping_lanes import ShippingLaneSegment
from app.db.session import get_db
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.get("", response_model=list[ShippingLaneSegment])
async def list_datasets(
    db: AsyncSession = Depends(get_db),
    limit: int | None = Query(
        None, description="Limit number of records returned (default: all)"),
) -> list[ShippingLaneSegment]:

    statement = (
        select(
            ShippingLane,
            func.ST_AsGeoJSON(ShippingLane.geom).label("geometry"),
        )
        .order_by(ShippingLane.id)
    )
    if limit:
        statement = statement.limit(limit)
        
    result = await db.execute(statement)
    rows = result.all()

    segments = [
        ShippingLaneSegment(
            id=segment.id,
            distance_km=float(segment.distance_km),
            geometry=json.loads(geometry) if geometry else None,
        )
        for segment, geometry in rows
    ]

    return segments
