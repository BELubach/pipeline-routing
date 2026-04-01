"""
Gas Pipeline Routing API
FastAPI router for pipeline network routing and analysis

Data Sources:
- IGGIELGN (SciGRID_gas) dataset - European gas transmission network
  See /api/v1/metadata/datasets/iggielgn for full attribution
"""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.models.pipeline_iggielgn import GenericNode, PipelineSegment
from app.schemas.pipeline import (
    BorderNodeDTO,
    GenericNodeDTO,
    UnifiedNodeDTO,
    PipelineSegmentDTO,
    RouteResponse,
    RouteSegment,
    NodesResponse,
    UnifiedNodesResponse,
    BorderNodesResponse,
    SegmentsResponse
)
from app.core.metadata import create_response_metadata

router = APIRouter()


@router.get("/nodes", response_model=NodesResponse)
async def get_nodes(
    country: str | None = Query(
        None, description="ISO 3166-1 alpha-2 country code"),
        limit: int | None = Query(
        None, description="Limit number of records returned (default: all)"),
    db: AsyncSession = Depends(get_db),
):
    """
    List pipeline nodes, optionally filtered by country.

    Data source: IGGIELGN (SciGRID_gas)
    See /api/v1/metadata/datasets/iggielgn for attribution
    """
    result = await db.execute(
        text("""
            SELECT
                id, name, country_code,
                ST_X(geom) AS lon,
                ST_Y(geom) AS lat
            FROM generic_nodes
            WHERE (CAST(:country AS text) IS NULL OR country_code = CAST(:country AS text))
            ORDER BY name
            """ + ("LIMIT :limit" if limit is not None else "")),
        {"country": country, "limit": limit} if limit is not None else {"country": country}
    )
    rows = result.fetchall()
    nodes = [
        GenericNodeDTO(
            id=r.id, name=r.name, country_code=r.country_code,
            lon=float(r.lon), lat=float(r.lat),
        )
        for r in rows
    ]

    # Create metadata
    filters = {"country": country} if country else None
    metadata = create_response_metadata(
        dataset_id="iggielgn",
        record_count=len(nodes),
        filters_applied=filters
    )

    return NodesResponse(data=nodes, metadata=metadata)


@router.get("/nodes-unified", response_model=UnifiedNodesResponse)
async def get_nodes_unified(
    country: str | None = Query(
        None, description="ISO 3166-1 alpha-2 country code"),
    limit: int | None = Query(
        None, description="Limit number of records returned (default: all)"),
    db: AsyncSession = Depends(get_db),
):
    """
    List all generic nodes with type classification.

    Returns all nodes from generic_nodes table with an additional 'node_type' field:
    - null: Standard generic node
    - 'border': Node also exists in border_nodes (matched by coordinates)
    - 'lng': Node also exists in lng_terminals (matched by coordinates)

    Uses efficient LEFT JOINs on geometry to avoid N+1 queries.
    """
    result = await db.execute(
        text("""
            SELECT 
                gn.id,
                gn.name,
                gn.country_code,
                ST_X(gn.geom) AS lon,
                ST_Y(gn.geom) AS lat,
                CASE 
                    WHEN lt.id IS NOT NULL THEN 'lng'
                    WHEN bn.id IS NOT NULL THEN 'border'
                    ELSE NULL
                END AS node_type
            FROM generic_nodes gn
            LEFT JOIN lng_terminals lt ON ST_Equals(gn.geom, lt.geom)
            LEFT JOIN border_nodes bn ON ST_Equals(gn.geom, bn.geom)
            WHERE (CAST(:country AS text) IS NULL OR gn.country_code = CAST(:country AS text))
            ORDER BY gn.name
                """ + ("LIMIT :limit" if limit is not None else "")),
        {"country": country, "limit": limit} if limit is not None else {"country": country}
    )
    rows = result.fetchall()
    nodes = [
        UnifiedNodeDTO(
            id=r.id,
            name=r.name,
            country_code=r.country_code,
            lon=float(r.lon),
            lat=float(r.lat),
            node_type=r.node_type,
        )
        for r in rows
    ]

    # Create metadata
    filters = {"country": country} if country else None
    metadata = create_response_metadata(
        dataset_id="iggielgn",
        record_count=len(nodes),
        filters_applied=filters
    )

    return UnifiedNodesResponse(data=nodes, metadata=metadata)


@router.get("/border-crossings", response_model=BorderNodesResponse)
async def get_border_nodes(
    db: AsyncSession = Depends(get_db),
    country: str | None = Query(
        None, description="Filter border crossings by country code (either side)"),
    limit: int | None = Query(
        None, description="Limit number of records returned (default: all)"),
):
    """Returns all border crossing nodes."""

    result = await db.execute(
        text("""
            SELECT
                id, name, country_code,
                ST_X(geom) AS lon, ST_Y(geom) AS lat,
                from_country, to_country, "from_TSO", "to_TSO"
            FROM border_nodes 
            WHERE (CAST(:country AS text) IS NULL OR country_code = CAST(:country AS text))
            ORDER BY name
            """ + ("LIMIT :limit" if limit is not None else "")),
        {"country": country, "limit": limit} if limit is not None else {"country": country}
    )
    rows = result.fetchall()
    nodes = [
        BorderNodeDTO(
            id=r.id, name=r.name, country_code=r.country_code,
            from_country=r.from_country, to_country=r.to_country,
            from_TSO=r.from_TSO, to_TSO=r.to_TSO,
            lon=float(r.lon), lat=float(r.lat),
        )
        for r in rows
    ]

    # Create metadata
    metadata = create_response_metadata(
        dataset_id="iggielgn",
        record_count=len(nodes)
    )

    return BorderNodesResponse(data=nodes, metadata=metadata)


@router.get('/segments', response_model=SegmentsResponse)
async def get_pipeline_segments(
    country: str | None = Query(
        None, description="Filter segments by country code (either end)"),
    is_h_gas: bool | None = Query(
        None, description="Filter by H-gas (True), L-gas (False), or both (None)"),
    limit: int | None = Query(
        None, description="Limit number of records returned (default: all)"),
    db: AsyncSession = Depends(get_db),
):
    """
    List pipeline segments with optional filters.

    Data source: IGGIELGN (SciGRID_gas)
    See /api/v1/metadata/datasets/iggielgn for attribution
    """


    statement = (
        select(
            PipelineSegment,
            func.ST_AsGeoJSON(PipelineSegment.geom).label("geometry"),
        )
        .order_by(PipelineSegment.id)
    )
    
    if limit: 
        statement = statement.limit(limit)

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

    segments = [
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

    # Create metadata
    filters = {}
    if country:
        filters["country"] = country
    if is_h_gas is not None:
        filters["is_h_gas"] = is_h_gas

    metadata = create_response_metadata(
        dataset_id="iggielgn",
        record_count=len(segments),
        total_records=10000 if len(
            segments) == 10000 else None,  # Indicate if limited
        filters_applied=filters if filters else None
    )

    return SegmentsResponse(data=segments, metadata=metadata)


@router.get('/route/{source_node_id}/{target_node_id}', response_model=RouteResponse)
async def get_route(
    source_node_id: int,
    target_node_id: int,
    directed: bool = Query(
        False, description="Whether to treat network as directed (default: False for bidirectional)"),
    db: AsyncSession = Depends(get_db),
):
    """
    Calculate the shortest route between two nodes using Dijkstra's algorithm.
    Uses the length_km property of segments as the cost/weight.

    Args:
        source_node_id: Starting node ID
        target_node_id: Destination node ID  
        directed: If False, allows travel in both directions on segments (default)

    Returns:
        RouteResponse with path segments and total distance
    """

    # First, verify that both nodes exist
    node_check = await db.execute(
        select(GenericNode.id)
        .where(GenericNode.id.in_([source_node_id, target_node_id]))
    )
    found_nodes = {row[0] for row in node_check.fetchall()}

    if source_node_id not in found_nodes:
        raise HTTPException(
            status_code=404, detail=f"Source node '{source_node_id}' not found")
    if target_node_id not in found_nodes:
        raise HTTPException(
            status_code=404, detail=f"Target node '{target_node_id}' not found")

    # Build routing query using pgr_dijkstra
    # pgr_dijkstra expects edges table with: id, source, target, cost, [reverse_cost]
    # We create a CTE that represents our graph
    # All parameters need explicit casts to disambiguate the function overload

    routing_query = text("""
        SELECT 
            r.seq,
            r.path_seq,
            r.node,
            r.edge,
            r.cost,
            r.agg_cost,
            ps.id AS segment_id,
            ps.from_node_id,
            ps.to_node_id,
            ps.length_km,
            ST_AsGeoJSON(ps.geom) AS geometry
        FROM pgr_dijkstra(
            'SELECT 
                id, 
                from_node_id AS source, 
                to_node_id AS target, 
                CAST(length_km AS float8) AS cost, 
                CAST(length_km AS float8) AS reverse_cost 
            FROM pipeline_segments 
            WHERE from_node_id IS NOT NULL 
              AND to_node_id IS NOT NULL 
              AND length_km > 0',
            CAST(:source_node AS INTEGER),
            CAST(:target_node AS INTEGER),
            CAST(:directed AS BOOLEAN)
        ) r
        LEFT JOIN pipeline_segments ps ON r.edge = ps.id
        ORDER BY r.path_seq
    """)

    result = await db.execute(
        routing_query,
        {"source_node": source_node_id,
            "target_node": target_node_id, "directed": directed}
    )
    rows = result.fetchall()

    if not rows:
        raise HTTPException(
            status_code=404,
            detail=f"No route found between '{source_node_id}' and '{target_node_id}'"
        )

    # Filter out the last row which has edge=-1 (destination node)
    path_segments = []
    for row in rows:
        if row.edge != -1:  # Skip destination node entry
            path_segments.append(
                RouteSegment(
                    segment_id=row.segment_id,
                    from_node_id=row.from_node_id,
                    to_node_id=row.to_node_id,
                    length_km=float(row.length_km),
                    geometry=json.loads(
                        row.geometry) if row.geometry else None,
                )
            )

    # Calculate total distance from the segments
    total_distance = sum(seg.length_km for seg in path_segments)

    # Create metadata
    metadata = create_response_metadata(
        dataset_id="iggielgn",
        record_count=len(path_segments),
        filters_applied={
            "source_node_id": source_node_id,
            "target_node_id": target_node_id,
            "directed": directed
        }
    )

    return RouteResponse(
        source_node_id=source_node_id,
        target_node_id=target_node_id,
        total_distance_km=round(total_distance, 2),
        num_segments=len(path_segments),
        path=path_segments,
        metadata=metadata
    )
