"""
Gas Pipeline Routing API
FastAPI router for pipeline network routing and analysis
"""

from __future__ import annotations

import json
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.models.pipeline_iggielgn import GenericNode, PipelineSegment
from app.schemas.pipeline import BorderNodeDTO, GenericNodeDTO, PipelineSegmentDTO

router = APIRouter()


# =============================================================
# Response models
# =============================================================

class RouteSegment(BaseModel):
    seq: int
    node_id: int | None
    node_name: str | None
    edge_id: int | None
    pipeline_name: str | None
    segment_cost_eur_mwh: float | None
    cumulative_cost_eur_mwh: float | None
    segment_km: float | None
    # GeoJSON geometry for this segment
    geometry: dict | None = Field(None, description="GeoJSON LineString")


class RouteResponse(BaseModel):
    source_lon: float
    source_lat: float
    dest_lon: float
    dest_lat: float
    start_node_id: int | None
    end_node_id: int | None
    start_snap_km: float | None
    end_snap_km: float | None
    total_cost_eur_mwh: float | None
    total_km: float | None
    cost_type: str
    segments: list[RouteSegment]
    route_geojson: dict = Field(
        description="Full route as GeoJSON FeatureCollection")


class NearestNode(BaseModel):
    node_id: int
    name: str
    node_type: str
    distance_km: float


class PipelineNode(BaseModel):
    id: int
    name: str
    node_type: str
    country: str | None
    is_trading_hub: bool
    hub_code: str | None
    lng_capacity_bcm: float | None
    lng_type: str | None
    lon: float
    lat: float


# =============================================================
# Endpoints
# =============================================================

@router.get("/route", response_model=RouteResponse)
async def get_cheapest_route(
    start_lon: float = Query(..., description="Source longitude (WGS84)"),
    start_lat: float = Query(..., description="Source latitude (WGS84)"),
    end_lon:   float = Query(..., description="Destination longitude (WGS84)"),
    end_lat:   float = Query(..., description="Destination latitude (WGS84)"),
    cost_type: Literal["composite", "tariff", "distance"] = Query(
        "composite",
        description="Cost metric to optimise: composite (default), tariff (€/MWh), distance (km)"
    ),
    max_snap_km: float = Query(
        200.0,
        description="Max distance in km to snap a coordinate to the nearest pipeline node"
    ),
    db: AsyncSession = Depends(get_db),
):
    """
    Find the cheapest gas pipeline route between two coordinates.

    Snaps start/end to nearest pipeline nodes, then runs pgRouting Dijkstra
    over the pipeline network with the selected cost metric.

    Returns the ordered list of segments with cumulative cost and GeoJSON geometry.
    """
    result = await db.execute(
        text("""
            SELECT
                seq,
                node_id,
                node_name,
                edge_id,
                pipeline_name,
                segment_cost,
                cumulative_cost,
                segment_km,
                ST_AsGeoJSON(geom)::json AS geometry,
                snap_info
            FROM route_by_coordinates(
                :start_lon, :start_lat,
                :end_lon,   :end_lat,
                :cost_type,
                :max_snap_km
            )
            ORDER BY seq
        """),
        {
            "start_lon": start_lon, "start_lat": start_lat,
            "end_lon": end_lon,     "end_lat": end_lat,
            "cost_type": cost_type,
            "max_snap_km": max_snap_km,
        }
    )
    rows = result.fetchall()

    if not rows:
        raise HTTPException(
            status_code=404,
            detail=f"No pipeline route found between ({start_lon},{start_lat}) "
                   f"and ({end_lon},{end_lat}). "
                   f"Check that both points are within {max_snap_km}km of a pipeline node."
        )

    # Parse snap info from first row
    snap_info = rows[0].snap_info or {}
    segments: list[RouteSegment] = []
    features = []

    for row in rows:
        seg = RouteSegment(
            seq=row.seq,
            node_id=row.node_id,
            node_name=row.node_name,
            edge_id=row.edge_id,
            pipeline_name=row.pipeline_name,
            segment_cost_eur_mwh=float(
                row.segment_cost) if row.segment_cost else None,
            cumulative_cost_eur_mwh=float(
                row.cumulative_cost) if row.cumulative_cost else None,
            segment_km=float(row.segment_km) if row.segment_km else None,
            geometry=row.geometry,
        )
        segments.append(seg)

        if row.geometry:
            features.append({
                "type": "Feature",
                "properties": {
                    "seq": row.seq,
                    "pipeline_name": row.pipeline_name,
                    "segment_cost_eur_mwh": float(row.segment_cost) if row.segment_cost else None,
                    "cumulative_cost_eur_mwh": float(row.cumulative_cost) if row.cumulative_cost else None,
                    "segment_km": float(row.segment_km) if row.segment_km else None,
                },
                "geometry": row.geometry,
            })

    last = rows[-1]
    total_cost = float(last.cumulative_cost) if last.cumulative_cost else None
    total_km = sum(float(s.segment_km) for s in segments if s.segment_km)

    return RouteResponse(
        source_lon=start_lon,
        source_lat=start_lat,
        dest_lon=end_lon,
        dest_lat=end_lat,
        start_node_id=snap_info.get("start_node_id"),
        end_node_id=snap_info.get("end_node_id"),
        start_snap_km=snap_info.get("start_snap_km"),
        end_snap_km=snap_info.get("end_snap_km"),
        total_cost_eur_mwh=total_cost,
        total_km=round(total_km, 2),
        cost_type=cost_type,
        segments=segments,
        route_geojson={
            "type": "FeatureCollection",
            "features": features,
        }
    )


@router.get("/nearest-nodes", response_model=list[NearestNode])
async def get_nearest_nodes(
    lon: float = Query(...),
    lat: float = Query(...),
    max_km: float = Query(200.0),
    node_type: str | None = Query(None, description="Filter by node type"),
    db: AsyncSession = Depends(get_db),
):
    """Return the 50 nearest pipeline nodes to a coordinate."""
    node_types = [node_type] if node_type else []
    result = await db.execute(
        text("""
            SELECT node_id, name, node_type, distance_km
            FROM nearest_node(
                :lon, :lat, :max_km, :node_types
            )
        """),
        {
            "lon": lon,
            "lat": lat,
            "max_km": max_km,
            "node_types": node_types,
        }
    )
    rows = result.fetchall()
    return [
        NearestNode(node_id=r.node_id, name=r.name,
                    node_type=r.node_type, distance_km=float(r.distance_km))
        for r in rows
    ]


@router.get("/nodes", response_model=list[GenericNodeDTO])
async def get_nodes(
    country: str | None = Query(
        None, description="ISO 3166-1 alpha-2 country code"),
    db: AsyncSession = Depends(get_db),
):
    """List pipeline nodes, optionally filtered by country."""
    result = await db.execute(
        text("""
            SELECT
                id, name, country_code,
                ST_X(geom) AS lon,
                ST_Y(geom) AS lat
            FROM generic_nodes
            WHERE (CAST(:country AS text) IS NULL OR country_code = CAST(:country AS text))
            ORDER BY name
            LIMIT 500
        """),
        {"country": country}
    )
    rows = result.fetchall()
    return [
        GenericNodeDTO(
            id=r.id, name=r.name,country_code=r.country_code,
            lon=float(r.lon), lat=float(r.lat),
        )
        for r in rows
    ]


@router.get("/nodes/{node_id}/reachable")
async def get_reachable_from_node(
    node_id: int,
    max_cost: float = Query(
        10.0, description="Max cost in €/MWh to consider reachable"),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns all nodes reachable from a given node within a cost budget.
    Uses pgr_drivingDistance — useful for the 'isochrone' / ChronoTrains effect.
    """
    result = await db.execute(
        text("""
            SELECT
                n.id, n.name, n.node_type, n.country,
                ST_X(n.geom) AS lon, ST_Y(n.geom) AS lat,
                dd.agg_cost AS cost_eur_mwh
            FROM pgr_drivingDistance(
                'SELECT id, source, target, cost_composite AS cost,
                        reverse_cost_composite AS reverse_cost
                 FROM pipeline_edges
                 WHERE status IN (''operating'', ''construction'')',
                CAST(:node_id AS BIGINT),
                CAST(:max_cost AS FLOAT),
                directed := true
            ) dd
            JOIN pipeline_nodes n ON n.id = dd.node
            WHERE dd.agg_cost > 0
            ORDER BY dd.agg_cost
        """),
        {"node_id": node_id, "max_cost": max_cost}
    )
    rows = result.fetchall()
    return {
        "source_node_id": node_id,
        "max_cost_eur_mwh": max_cost,
        "reachable_count": len(rows),
        "nodes": [
            {
                "id": r.id, "name": r.name, "node_type": r.node_type,
                "country": r.country, "lon": float(r.lon), "lat": float(r.lat),
                "cost_eur_mwh": round(float(r.cost_eur_mwh), 4),
            }
            for r in rows
        ]
    }


@router.get("/border-crossings", response_model=list[BorderNodeDTO])
async def get_border_nodes(
    db: AsyncSession = Depends(get_db),
):
    """Returns all border crossing nodes."""

    result = await db.execute(
        text("""
            SELECT
                id, name, country_code,
                ST_X(geom) AS lon, ST_Y(geom) AS lat,
                from_country, to_country, "from_TSO", "to_TSO"
            FROM border_nodes
            ORDER BY name
        """)
    )
    rows = result.fetchall()
    return [
        BorderNodeDTO(
            id=r.id, name=r.name, country_code=r.country_code,
            from_country=r.from_country, to_country=r.to_country,
            from_TSO=r.from_TSO, to_TSO=r.to_TSO,
            lon=float(r.lon), lat=float(r.lat),
        )
        for r in rows
    ]



@router.get('/segments', response_model=list[PipelineSegmentDTO])
async def get_pipeline_segments(
    country: str | None = Query(
        None, description="Filter segments by country code (either end)"),
    is_h_gas: bool | None = Query(
        None, description="Filter by H-gas (True), L-gas (False), or both (None)"),
    db: AsyncSession = Depends(get_db),
):
    """List pipeline segments with optional filters."""
    statement = (
        select(
            PipelineSegment,
            func.ST_AsGeoJSON(PipelineSegment.geom).label("geometry"),
        )
        .order_by(PipelineSegment.id)
        .limit(1000)
    )

    if country:
        statement = statement.where(
            or_(
                PipelineSegment.country_code_from == country,
                PipelineSegment.country_code_to == country,
            )
        )
    if is_h_gas is not None:
        statement = statement.where(PipelineSegment.is_H_gas == is_h_gas)

    result = await db.execute(statement)
    rows = result.all()

    return [
        PipelineSegmentDTO(
            id=segment.id,
            from_node=segment.from_node_id,
            to_node=segment.to_node_id,
            length_km=float(segment.length_km),
            IGGIELGN_id=segment.IGGIELGN_id,
            country_code_from=segment.country_code_from,
            country_code_to=segment.country_code_to,
            is_H_gas=segment.is_H_gas,
            geometry=json.loads(geometry) if geometry else None,
        )
        for segment, geometry in rows
    ]