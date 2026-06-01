"""
Routing service layer - handles all routing business logic
"""
from typing import List, Dict, Any
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.routing import RouteNode, NeighborNode, RouteSummary



async def find_shortest_path(
    db: AsyncSession,
    start_node_id: int,
    end_node_id: int
) -> List[RouteNode]:
    """
    Find the shortest path between two nodes by distance.
    
    Args:
        db: Database session
        start_node_id: Starting node ID
        end_node_id: Ending node ID
        
    Returns:
        List of RouteNode objects representing the path
        
    Raises:
        ValueError: If no path is found
    """
    
    result = await db.execute(
        text("""
            SELECT seq, node_id, node_name, edge_id, distance_km, total_distance
            FROM find_shortest_path(:start_id, :end_id)
        """),
        {"start_id": start_node_id, "end_id": end_node_id}
    )
    
    rows = result.fetchall()
    
    if not rows:
        raise ValueError(f"No path found between nodes {start_node_id} and {end_node_id}")
    
    path = [
        RouteNode(
            seq=row.seq,
            node_id=row.node_id,
            node_name=row.node_name,
            edge_id=row.edge_id,
            distance_km=float(row.distance_km) if row.distance_km else None,
            total_distance=float(row.total_distance)
        )
        for row in rows
    ]
    
    return path


async def get_node_neighbors(
    db: AsyncSession,
    node_id: int
) -> List[NeighborNode]:
    """
    Get all nodes directly connected to a given node.
    
    Args:
        db: Database session
        node_id: Node ID to find neighbors for
        
    Returns:
        List of NeighborNode objects
    """
    print(f"👥 Finding neighbors for node {node_id}")
    
    result = await db.execute(
        text("""
            SELECT neighbor_id, neighbor_name, distance_km, segment_id
            FROM get_node_neighbors(:node_id)
        """),
        {"node_id": node_id}
    )
    
    rows = result.fetchall()
    
    neighbors = [
        NeighborNode(
            neighbor_id=row.neighbor_id,
            neighbor_name=row.neighbor_name,
            distance_km=float(row.distance_km),
            segment_id=row.segment_id
        )
        for row in rows
    ]
    
    return neighbors


async def check_nodes_connected(
    db: AsyncSession,
    node_a: int,
    node_b: int
) -> Dict[str, Any]:
    """
    Check if two nodes are connected (i.e., if a path exists between them).
    
    Args:
        db: Database session
        node_a: First node ID
        node_b: Second node ID
        
    Returns:
        Dict with node_a, node_b, and connected (bool) keys
    """
    
    result = await db.execute(
        text("SELECT check_nodes_connected(:node_a, :node_b) as connected"),
        {"node_a": node_a, "node_b": node_b}
    )
    
    row = result.fetchone()
    
    connected = {
        "node_a": node_a,
        "node_b": node_b,
        "connected": row.connected
    }
    
    return connected


async def get_route_summary(
    db: AsyncSession,
    start_node_id: int,
    end_node_id: int
) -> RouteSummary:
    """
    Get summary statistics about a route between two nodes.
    
    Args:
        db: Database session
        start_node_id: Starting node ID
        end_node_id: Ending node ID
        
    Returns:
        RouteSummary object
        
    Raises:
        ValueError: If no path is found
    """
    
    result = await db.execute(
        text("""
            SELECT start_node, end_node, total_distance, segment_count, node_count
            FROM get_route_summary(:start_id, :end_id)
        """),
        {"start_id": start_node_id, "end_id": end_node_id}
    )
    
    row = result.fetchone()
    
    if not row or row.total_distance is None:
        raise ValueError(f"No path found between nodes {start_node_id} and {end_node_id}")
    
    summary = RouteSummary(
        start_node=row.start_node,
        end_node=row.end_node,
        total_distance=float(row.total_distance),
        segment_count=row.segment_count,
        node_count=row.node_count
    )
    
    return summary
