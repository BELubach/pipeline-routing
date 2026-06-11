from typing import Optional, Any
from pydantic import BaseModel

class RouteNode(BaseModel):
    seq: int
    edge_id: Optional[int]
    start_node: Optional[int]
    end_node: Optional[int]
    distance_km: Optional[float]
    total_distance: float
    geometry: Optional[dict] = None


class NeighborNode(BaseModel):
    neighbor_id: int
    neighbor_name: Optional[str]
    distance_km: float
    segment_id: int


class RouteSummary(BaseModel):
    start_node: int
    end_node: int
    total_distance: float
    segment_count: int
    node_count: int
