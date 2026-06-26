
import json
from select import select

from fastapi import APIRouter, Depends, Depends, Query
from sqlalchemy import func, select
from app.db.session import get_db
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.base import Node, Segment
from app.models.maritime_routes import MaritimeRoutes as MaritimeRouteModel
from app.models.maritime_routes import MaritimeRoutesVertices
router = APIRouter()


@router.get("/segments", response_model=list[Segment])
async def list_datasets(
    db: AsyncSession = Depends(get_db),
    limit: int | None = Query(
        None, description="Limit number of records returned (default: all)"),
) -> list[Segment]:

    statement = (
        select(
            MaritimeRouteModel,
            func.ST_AsGeoJSON(MaritimeRouteModel.geometry).label("geometry"),
        )
    )
    if limit:
        statement = statement.limit(limit)
        
    result = await db.execute(statement)
    rows = result.all()
    segments = [
        Segment(
            id=route.id,
            from_node=route.source,
            to_node=route.target,
            geometry=json.loads(geometry) if geometry else None,
        )
        for route, geometry in rows
    ]

    return segments


@router.get("/nodes", response_model=list[Node])
async def list_maritime_route_nodes(
    db: AsyncSession = Depends(get_db),
    limit: int | None = Query(
        None, description="Limit number of records returned (default: all)"),
) -> list[Node]:

    statement = (
        select(
            MaritimeRoutesVertices
        )
    )
    if limit:
        statement = statement.limit(limit)

    result = await db.execute(statement)
    rows = result.all()
    nodes = [
        Node(
            id=node.id,
            lat=node.y,
            lon=node.x,

        )
        for node, in rows
    ]

    return nodes