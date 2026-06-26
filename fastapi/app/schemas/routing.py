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


class NetworkNodeType(str):
    pipeline = "pipeline"
    maritime = "maritime"


class InterNetworkNode(BaseModel):
    id: int
    node_type: str  # 'pipeline' | 'maritime'


class RouteRequest(BaseModel):
    start: InterNetworkNode
    end: InterNetworkNode


class RouteStep(BaseModel):
    seq: int
    node_id: int
    node_type: str
    edge_id: int
    segment_km: float
    cumulative_km: float
    network: str


class RouteResponse(BaseModel):
    start: InterNetworkNode
    end: InterNetworkNode
    total_km: float
    steps: list[RouteStep]


class InterNetworkRouteStep(BaseModel):
    seq: int
    node_id: int           # external id (maritime offset removed)
    node_type: str         # 'pipeline' | 'maritime'
    edge_id: int
    segment_km: float
    cumulative_km: float
    network: str           # 'pipeline' | 'maritime' | 'terminal_bridge' | 'unknown'


class InterNetworkRouteResult(BaseModel):
    start_node_id: int
    start_node_type: str
    end_node_id: int
    end_node_type: str
    total_km: float
    steps: list[InterNetworkRouteStep]
