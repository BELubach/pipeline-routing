from typing import Optional
from pydantic import BaseModel

class RouteNode(BaseModel):
    seq: int
    node_id: int
    node_name: Optional[str]
    edge_id: Optional[int]
    distance_km: Optional[float]
    total_distance: float


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
