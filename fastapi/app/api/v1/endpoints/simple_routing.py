from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services import routing as routing_service
from app.schemas.routing import RouteNode, NeighborNode, RouteSummary
router = APIRouter()




@router.get("/path/{start_node_id}/{end_node_id}", response_model=List[RouteNode])
async def get_shortest_path(
    start_node_id: int,
    end_node_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Find the shortest path between two nodes by distance.
    
    Simple distance-based routing through the pipeline network.
    """
    try:
        path = await routing_service.find_shortest_path(db, start_node_id, end_node_id)
        
        return [
            RouteNode(
                seq=node.seq,
                edge_id=node.edge_id,
                start_node=node.start_node,
                end_node=node.end_node,
                distance_km=node.distance_km,
                total_distance=node.total_distance,
                geometry=node.geometry,
            )
            for node in path
        ]
        
    except ValueError as e:
        print(e)
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/neighbors/{node_id}", response_model=List[NeighborNode])
async def get_neighbors(
    node_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get all nodes directly connected to a given node.
    """
    try:
        neighbors = await routing_service.get_node_neighbors(db, node_id)
        
        return [
            NeighborNode(
                neighbor_id=neighbor.neighbor_id,
                neighbor_name=neighbor.neighbor_name,
                distance_km=neighbor.distance_km,
                segment_id=neighbor.segment_id
            )
            for neighbor in neighbors
        ]
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/connected/{node_a}/{node_b}")
async def check_connected(
    node_a: int,
    node_b: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Check if two nodes are connected (i.e., if a path exists between them).
    """
    try:
        return await routing_service.check_nodes_connected(db, node_a, node_b)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary/{start_node_id}/{end_node_id}", response_model=RouteSummary)
async def get_summary(
    start_node_id: int,
    end_node_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get summary statistics about a route between two nodes.
    """
    try:
        summary = await routing_service.get_route_summary(db, start_node_id, end_node_id)
        
        return RouteSummary(
            start_node=summary.start_node,
            end_node=summary.end_node,
            total_distance=summary.total_distance,
            segment_count=summary.segment_count,
            node_count=summary.node_count
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
