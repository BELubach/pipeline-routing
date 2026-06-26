from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import text
from typing import Optional, List
from pydantic import BaseModel, Field
from app.db.session import SessionLocal

router = APIRouter()


# Pydantic models for request/response
class RouteSegment(BaseModel):
    seq: int
    path_node: str
    node_name: Optional[str]
    node_type: Optional[str]
    edge_id: Optional[str]
    edge_type: Optional[str]
    segment_cost: Optional[float]
    cumulative_cost: Optional[float]
    segment_km: Optional[float]


class RouteResponse(BaseModel):
    route: List[RouteSegment]
    snap_info: Optional[dict] = None
    total_distance_km: Optional[float] = None
    total_cost: Optional[float] = None


class NodeInfo(BaseModel):
    node_id: str
    name: Optional[str]
    node_type: str
    distance_km: float
    lon: Optional[float] = None
    lat: Optional[float] = None


class TerminalConnection(BaseModel):
    terminal_id: int
    terminal_name: Optional[str]
    country_code: Optional[str]
    capacity_m3_per_d: Optional[float]
    pipeline_connections: int
    shipping_connections: int
    total_connections: int


class RouteSummary(BaseModel):
    total_distance_km: float
    total_cost: float
    pipeline_km: Optional[float]
    shipping_km: Optional[float]
    terminal_transfers: int
    segment_count: int


class ModeAnalysis(BaseModel):
    mode_type: str
    segment_count: int
    total_distance_km: float
    total_cost: float
    lng_terminal_stops: int


@router.get("/route/coordinates", response_model=RouteResponse, summary="Calculate route between coordinates")
async def route_by_coordinates(
    start_lon: float = Query(..., description="Start longitude", ge=-180, le=180),
    start_lat: float = Query(..., description="Start latitude", ge=-90, le=90),
    end_lon: float = Query(..., description="End longitude", ge=-180, le=180),
    end_lat: float = Query(..., description="End latitude", ge=-90, le=90),
    allow_shipping: bool = Query(True, description="Allow shipping lanes in route"),
    max_snap_km: float = Query(200.0, description="Maximum distance to snap to nearest node (km)", gt=0),
):
    """
    Calculate the optimal multimodal route between two geographic coordinates.
    
    The route can include:
    - Pipeline segments
    - Shipping lanes (if allow_shipping=True)
    - Modal transfers via LNG terminals
    
    Coordinates are automatically snapped to the nearest network node.
    """
    db = SessionLocal()
    try:
        result = db.execute(
            text("""
                SELECT 
                    seq, path_node, node_name, node_type, 
                    edge_id, edge_type, segment_cost, 
                    cumulative_cost, segment_km, snap_info
                FROM route_by_coordinates(
                    :start_lon, :start_lat, :end_lon, :end_lat, 
                    :allow_shipping, :max_snap_km
                )
            """),
            {
                "start_lon": start_lon,
                "start_lat": start_lat,
                "end_lon": end_lon,
                "end_lat": end_lat,
                "allow_shipping": allow_shipping,
                "max_snap_km": max_snap_km,
            }
        )
        
        rows = result.fetchall()
        
        if not rows:
            raise HTTPException(
                status_code=404, 
                detail="No route found between the specified coordinates"
            )
        
        route_segments = []
        snap_info = None
        
        for row in rows:
            route_segments.append(RouteSegment(
                seq=row.seq,
                path_node=row.path_node,
                node_name=row.node_name,
                node_type=row.node_type,
                edge_id=row.edge_id,
                edge_type=row.edge_type,
                segment_cost=float(row.segment_cost) if row.segment_cost else None,
                cumulative_cost=float(row.cumulative_cost) if row.cumulative_cost else None,
                segment_km=float(row.segment_km) if row.segment_km else None,
            ))
            if row.snap_info:
                snap_info = row.snap_info
        
        # Calculate totals
        total_distance = sum(s.segment_km for s in route_segments if s.segment_km) if route_segments else 0
        total_cost = route_segments[-1].cumulative_cost if route_segments else 0
        
        return RouteResponse(
            route=route_segments,
            snap_info=snap_info,
            total_distance_km=total_distance,
            total_cost=total_cost,
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.get("/route/nodes", response_model=List[RouteSegment], summary="Calculate route between node IDs")
async def route_by_nodes(
    start_node: str = Query(..., description="Start node ID (e.g., 'generic_123')"),
    end_node: str = Query(..., description="End node ID (e.g., 'generic_456')"),
    allow_shipping: bool = Query(True, description="Allow shipping lanes in route"),
):
    """
    Calculate the optimal multimodal route between two specific nodes.
    
    Node IDs must be prefixed with their type:
    - generic_XXX for generic nodes
    - border_XXX for border nodes
    - lng_XXX for LNG terminals
    """
    db = SessionLocal()
    try:
        result = db.execute(
            text("""
                SELECT 
                    seq, path_node, node_name, node_type, 
                    edge_id, edge_type, segment_cost, 
                    cumulative_cost, segment_km
                FROM find_multimodal_route(:start_node, :end_node, :allow_shipping)
            """),
            {
                "start_node": start_node,
                "end_node": end_node,
                "allow_shipping": allow_shipping,
            }
        )
        
        rows = result.fetchall()
        
        if not rows:
            raise HTTPException(
                status_code=404, 
                detail=f"No route found between {start_node} and {end_node}"
            )
        
        return [
            RouteSegment(
                seq=row.seq,
                path_node=row.path_node,
                node_name=row.node_name,
                node_type=row.node_type,
                edge_id=row.edge_id,
                edge_type=row.edge_type,
                segment_cost=float(row.segment_cost) if row.segment_cost else None,
                cumulative_cost=float(row.cumulative_cost) if row.cumulative_cost else None,
                segment_km=float(row.segment_km) if row.segment_km else None,
            )
            for row in rows
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.get("/route/summary", response_model=RouteSummary, summary="Get route summary statistics")
async def get_route_summary(
    start_node: str = Query(..., description="Start node ID"),
    end_node: str = Query(..., description="End node ID"),
    allow_shipping: bool = Query(True, description="Allow shipping lanes"),
):
    """
    Get a statistical summary of a route including:
    - Total distance and cost
    - Distance by mode (pipeline vs shipping)
    - Number of terminal transfers
    - Total segment count
    """
    db = SessionLocal()
    try:
        result = db.execute(
            text("""
                SELECT 
                    total_distance_km, total_cost, pipeline_km, 
                    shipping_km, terminal_transfers, segment_count
                FROM get_route_summary(:start_node, :end_node, :allow_shipping)
            """),
            {
                "start_node": start_node,
                "end_node": end_node,
                "allow_shipping": allow_shipping,
            }
        )
        
        row = result.fetchone()
        
        if not row:
            raise HTTPException(
                status_code=404, 
                detail=f"No route found between {start_node} and {end_node}"
            )
        
        return RouteSummary(
            total_distance_km=float(row.total_distance_km) if row.total_distance_km else 0,
            total_cost=float(row.total_cost) if row.total_cost else 0,
            pipeline_km=float(row.pipeline_km) if row.pipeline_km else None,
            shipping_km=float(row.shipping_km) if row.shipping_km else None,
            terminal_transfers=row.terminal_transfers or 0,
            segment_count=row.segment_count or 0,
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.get("/route/analyze", response_model=List[ModeAnalysis], summary="Analyze route by transport mode")
async def analyze_route(
    start_node: str = Query(..., description="Start node ID"),
    end_node: str = Query(..., description="End node ID"),
    allow_shipping: bool = Query(True, description="Allow shipping lanes"),
):
    """
    Analyze a route to understand the distribution of transport modes.
    
    Returns breakdown by:
    - Pipeline segments
    - Shipping segments
    - Terminal connections
    - Total distance and cost per mode
    """
    db = SessionLocal()
    try:
        result = db.execute(
            text("""
                SELECT 
                    mode_type, segment_count, total_distance_km, 
                    total_cost, lng_terminal_stops
                FROM analyze_route_modes(:start_node, :end_node, :allow_shipping)
            """),
            {
                "start_node": start_node,
                "end_node": end_node,
                "allow_shipping": allow_shipping,
            }
        )
        
        rows = result.fetchall()
        
        if not rows:
            raise HTTPException(
                status_code=404, 
                detail=f"No route found between {start_node} and {end_node}"
            )
        
        return [
            ModeAnalysis(
                mode_type=row.mode_type or "unknown",
                segment_count=row.segment_count or 0,
                total_distance_km=float(row.total_distance_km) if row.total_distance_km else 0,
                total_cost=float(row.total_cost) if row.total_cost else 0,
                lng_terminal_stops=row.lng_terminal_stops or 0,
            )
            for row in rows
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.get("/nodes/nearest", response_model=List[NodeInfo], summary="Find nearest nodes to coordinates")
async def find_nearest_nodes(
    lon: float = Query(..., description="Longitude", ge=-180, le=180),
    lat: float = Query(..., description="Latitude", ge=-90, le=90),
    max_dist_km: float = Query(200.0, description="Maximum search distance (km)", gt=0),
    node_types: Optional[str] = Query(
        None, 
        description="Comma-separated node types to filter (e.g., 'generic,lng_terminal')"
    ),
):
    """
    Find the nearest network nodes to a geographic coordinate.
    
    Optional filtering by node types:
    - generic: Regular pipeline nodes
    - border: Border crossing nodes
    - lng_terminal: LNG terminal nodes
    """
    db = SessionLocal()
    try:
        # Parse node_types if provided
        node_types_array = None
        if node_types:
            node_types_array = [nt.strip() for nt in node_types.split(",")]
        
        params = {
            "lon": lon,
            "lat": lat,
            "max_dist_km": max_dist_km,
        }
        
        if node_types_array:
            # Use ARRAY constructor for PostgreSQL
            query = text("""
                SELECT node_id, name, node_type, distance_km, 
                       ST_X(geom) as lon, ST_Y(geom) as lat
                FROM nearest_node(:lon, :lat, :max_dist_km, ARRAY[:node_types]::TEXT[])
            """)
            params["node_types"] = node_types_array
        else:
            query = text("""
                SELECT node_id, name, node_type, distance_km,
                       ST_X(geom) as lon, ST_Y(geom) as lat
                FROM nearest_node(:lon, :lat, :max_dist_km, NULL)
            """)
        
        result = db.execute(query, params)
        rows = result.fetchall()
        
        return [
            NodeInfo(
                node_id=row.node_id,
                name=row.name,
                node_type=row.node_type,
                distance_km=float(row.distance_km),
                lon=float(row.lon) if row.lon else None,
                lat=float(row.lat) if row.lat else None,
            )
            for row in rows
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.get("/terminals/connections", response_model=List[TerminalConnection], summary="Get LNG terminal connectivity")
async def get_terminal_connections():
    """
    Get all LNG terminals with their network connectivity information.
    
    Shows:
    - Number of pipeline connections
    - Number of shipping lane connections
    - Total connectivity
    - Terminal capacity
    
    Useful for identifying modal switching hubs.
    """
    db = SessionLocal()
    try:
        result = db.execute(
            text("""
                SELECT 
                    terminal_id, terminal_name, country_code, 
                    capacity_m3_per_d, pipeline_connections, 
                    shipping_connections, total_connections
                FROM get_lng_terminal_connections()
            """)
        )
        
        rows = result.fetchall()
        
        return [
            TerminalConnection(
                terminal_id=row.terminal_id,
                terminal_name=row.terminal_name,
                country_code=row.country_code,
                capacity_m3_per_d=float(row.capacity_m3_per_d) if row.capacity_m3_per_d else None,
                pipeline_connections=row.pipeline_connections or 0,
                shipping_connections=row.shipping_connections or 0,
                total_connections=row.total_connections or 0,
            )
            for row in rows
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.get("/terminals/nearest", response_model=List[NodeInfo], summary="Find nearest LNG terminals")
async def find_nearest_terminals(
    lon: float = Query(..., description="Longitude", ge=-180, le=180),
    lat: float = Query(..., description="Latitude", ge=-90, le=90),
    max_dist_km: float = Query(500.0, description="Maximum search distance (km)", gt=0),
):
    """
    Find the nearest LNG terminals to a geographic coordinate.
    
    LNG terminals are critical for:
    - Modal switching between pipeline and shipping
    - LNG import/export points
    - Network connectivity hubs
    """
    db = SessionLocal()
    try:
        result = db.execute(
            text("""
                SELECT 
                    terminal_id, terminal_name as name, 
                    'lng_terminal' as node_type, distance_km,
                    ST_X(geom) as lon, ST_Y(geom) as lat
                FROM find_nearest_lng_terminal(:lon, :lat, :max_dist_km)
            """),
            {
                "lon": lon,
                "lat": lat,
                "max_dist_km": max_dist_km,
            }
        )
        
        rows = result.fetchall()
        
        return [
            NodeInfo(
                node_id=f"lng_{row.terminal_id}",
                name=row.name,
                node_type=row.node_type,
                distance_km=float(row.distance_km),
                lon=float(row.lon) if row.lon else None,
                lat=float(row.lat) if row.lat else None,
            )
            for row in rows
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.post("/topology/refresh", summary="Refresh routing topology")
async def refresh_topology():
    """
    Refresh the routing topology materialized views.
    
    Call this after:
    - Adding/updating pipeline segments
    - Adding/updating shipping lanes
    - Adding/updating terminals
    - Any changes to node or edge data
    
    This rebuilds the unified network graph.
    """
    db = SessionLocal()
    try:
        db.execute(text("SELECT refresh_routing_topology()"))
        db.commit()
        return {"status": "success", "message": "Routing topology refreshed"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.post("/terminals/connect", summary="Create terminal network connections")
async def connect_terminals(
    max_pipeline_km: float = Query(50.0, description="Max distance to connect terminals to pipelines (km)", gt=0),
    max_shipping_km: float = Query(100.0, description="Max distance to connect terminals to shipping (km)", gt=0),
):
    """
    Create/update virtual edges connecting LNG terminals to the network.
    
    This connects terminals to:
    - Nearby pipeline nodes (within max_pipeline_km)
    - Nearby shipping lane endpoints (within max_shipping_km)
    
    Call this after refreshing topology or when adjusting connection distances.
    """
    db = SessionLocal()
    try:
        result = db.execute(
            text("""
                SELECT edge_count, pipeline_connections, shipping_connections
                FROM create_terminal_connections(:max_pipeline_km, :max_shipping_km)
            """),
            {
                "max_pipeline_km": max_pipeline_km,
                "max_shipping_km": max_shipping_km,
            }
        )
        
        row = result.fetchone()
        
        return {
            "status": "success",
            "total_edges": row.edge_count if row else 0,
            "pipeline_connections": row.pipeline_connections if row else 0,
            "shipping_connections": row.shipping_connections if row else 0,
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()