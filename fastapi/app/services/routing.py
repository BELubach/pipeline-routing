"""
Routing service layer - handles all routing business logic
"""
import json
from typing import List, Dict, Any
from unittest import result
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.routing import RouteNode, NeighborNode, RouteSummary, InterNetworkRouteStep, InterNetworkRouteResult



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
            SELECT seq, edge_id, start_node, end_node, distance_km, total_distance, geometry
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
            edge_id=row.edge_id,
            start_node=row.start_node,
            end_node=row.end_node,
            distance_km=float(row.distance_km) if row.distance_km else None,
            total_distance=float(row.total_distance),
            geometry=json.loads(row.geometry) if row.geometry else None,
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
    
    exists = await db.execute(
        text("SELECT 1 FROM generic_nodes WHERE id = :node_id"),
        {"node_id": node_id}
    )
    if not exists.fetchone():
        raise ValueError(f"Node {node_id} does not exist")

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


# Offset applied to maritime node IDs to keep them distinct from pipeline node IDs
# in the unified_network pgRouting graph.
MARITIME_NODE_OFFSET = 10_000_000


async def get_internetwork_route(
    db: AsyncSession,
    start_node_id: int,
    start_node_type: str,
    end_node_id: int,
    end_node_type: str,
) -> InterNetworkRouteResult:
    """
    Find the shortest route between any two nodes across the unified pipeline
    and maritime network.

    Pipeline nodes are stored with their natural IDs; maritime nodes are offset
    by MARITIME_NODE_OFFSET inside the unified_network table so their IDs never
    clash with pipeline node IDs.  This function handles the translation
    transparently so callers always work with the original (external) IDs.

    Args:
        db: Database session
        start_node_id: External ID of the starting node
        start_node_type: 'pipeline' or 'maritime'
        end_node_id: External ID of the destination node
        end_node_type: 'pipeline' or 'maritime'

    Returns:
        InterNetworkRouteResult containing each hop with its network type and
        cumulative distance in kilometres.

    Raises:
        ValueError: If no route exists between the two nodes.
    """

    def _to_internal(node_id: int, node_type: str) -> int:
        return node_id + MARITIME_NODE_OFFSET if node_type == "maritime" else node_id

    def _to_external(internal_id: int) -> tuple[int, str]:
        if internal_id >= MARITIME_NODE_OFFSET:
            return internal_id - MARITIME_NODE_OFFSET, "maritime"
        return internal_id, "pipeline"

    start_internal = _to_internal(start_node_id, start_node_type)
    end_internal   = _to_internal(end_node_id, end_node_type)
    print(start_internal, end_internal)
    result = await db.execute(
    text("""
        SELECT
            r.seq,
            r.node,
            r.edge,
            r.cost AS segment_km,
            SUM(r.cost) OVER (ORDER BY r.seq ROWS UNBOUNDED PRECEDING) AS cumulative_km,
            u.network
        FROM pgr_dijkstra(
            'SELECT id, source, target, cost FROM unified_network',
            CAST(:start_id AS BIGINT), -- Safe bind param + standard SQL cast
            CAST(:end_id AS BIGINT),   -- Safe bind param + standard SQL cast
            false 
        ) AS r
        LEFT JOIN unified_network u ON u.id = r.edge
        ORDER BY r.seq
    """),
    {"start_id": start_internal, "end_id": end_internal}, # This dictionary is now actively used!
)

    rows = result.fetchall()

    if not rows:
        raise ValueError(
            f"No route found between "
            f"{start_node_type} node {start_node_id} and "
            f"{end_node_type} node {end_node_id}"
        )

    steps: list[InterNetworkRouteStep] = []
    for row in rows:
        if row.edge == -1:
            # pgRouting appends a terminal sentinel row with edge = -1; skip it.
            continue

        node_id, node_type = _to_external(row.node)
        

        steps.append(
            InterNetworkRouteStep(
                seq=row.seq,
                node_id=node_id,
                node_type=node_type,
                edge_id=row.edge,
                segment_km=round(float(row.segment_km), 3),
                cumulative_km=round(float(row.cumulative_km), 3),
                network=row.network or "unknown",
            )
        )

    total_km = steps[-1].cumulative_km if steps else 0.0

    return InterNetworkRouteResult(
        start_node_id=start_node_id,
        start_node_type=start_node_type,
        end_node_id=end_node_id,
        end_node_type=end_node_type,
        total_km=round(total_km, 3),
        steps=steps,
    )


