from datetime import date
from typing import Any, Optional

from pydantic import BaseModel
from app.schemas.metadata import ResponseMetadata



class Node(BaseModel):
    id: int
    lat: float
    lon: float

class BorderNodeDTO(Node):
    
    name: str
    country_code: str
    from_country: str
    to_country: str
    from_TSO: Optional[str] = None
    to_TSO: Optional[str] = None

class GenericNodeDTO(Node):
    name: Optional[str] = None
    country_code: Optional[str] = None


class UnifiedNodeDTO(Node):
    """Unified node with type classification (null, 'border', or 'lng')"""
    name: Optional[str] = None
    country_code: Optional[str] = None
    node_type: Optional[str] = None  


class Segment(BaseModel):
    id: int
    from_node: Optional[int] = None 
    to_node: Optional[int] = None
    length_km: Optional[float] = None


class PipelineSegmentDTO(Segment):
    IGGIELGN_id: Optional[str] = None
    country_code_from: Optional[str] = None
    country_code_to: Optional[str] = None
    is_H_gas: bool = True
    geometry: dict | None = None


class GEMPipelineDTO(Segment):
    project_id: str
    pipeline_name: str
    segment_name: Optional[str] = None
    wiki: Optional[str] = None
    status: Optional[str] = None
    last_updated: Optional[date] = None
    fuel: Optional[str] = None
    countries_or_areas: Optional[str] = None
    owner: Optional[str] = None
    parent: Optional[str] = None
    parent_entity_ids: Optional[list[str]] = None
    start_year_1: Optional[int] = None
    start_year_2: Optional[int] = None
    start_year_3: Optional[int] = None
    shelved_year: Optional[int] = None
    cancelled_year: Optional[int] = None
    stop_year: Optional[int] = None
    capacity: Optional[float] = None
    capacity_units: Optional[str] = None
    capacity_bcm_y: Optional[float] = None
    capacity_boe_d: Optional[float] = None
    length_known_km: Optional[float] = None
    length_estimate_km: Optional[float] = None
    length_merged_km: Optional[float] = None
    diameter_raw: Optional[str] = None
    diameter_units: Optional[str] = None
    start_country_or_area: Optional[str] = None
    start_state_province: Optional[str] = None
    start_prefecture_district: Optional[str] = None
    end_location: Optional[str] = None
    end_country_or_area: Optional[str] = None
    end_state_province: Optional[str] = None
    end_prefecture_district: Optional[str] = None
    route_accuracy: Optional[str] = None
    route_type: Optional[str] = None
    raw_properties: Any = None

class GEMRouteSegment(BaseModel): 
    id: int
    pipeline_name: str
    geometry: dict | None = None
    length_km: Optional[float] = None

class RouteSegment(BaseModel):
    """A segment in a route path"""
    segment_id: int
    from_node_id: int
    to_node_id: int
    length_km: float
    geometry: dict | None = None


class RouteResponse(BaseModel):
    """Complete route between two nodes"""
    source_node_id: int
    target_node_id: int
    total_distance_km: float
    num_segments: int
    path: list[RouteSegment]
    metadata: ResponseMetadata


# List responses with metadata
class NodesResponse(BaseModel):
    """Response containing nodes with metadata"""
    data: list[GenericNodeDTO]
    metadata: ResponseMetadata


class UnifiedNodesResponse(BaseModel):
    """Response containing unified nodes with metadata"""
    data: list[UnifiedNodeDTO]
    metadata: ResponseMetadata


class BorderNodesResponse(BaseModel):
    """Response containing border nodes with metadata"""
    data: list[BorderNodeDTO]
    metadata: ResponseMetadata


class SegmentsResponse(BaseModel):
    """Response containing pipeline segments with metadata"""
    data: list[PipelineSegmentDTO]
    metadata: ResponseMetadata


class GEMSegmentsResponse(BaseModel):
    """Response containing GEM pipeline segments with metadata"""
    data: list[GEMRouteSegment]
    metadata: ResponseMetadata

class GEMPipelinesResponse(BaseModel):
    """Response containing GEM pipeline details with metadata"""
    data: list[GEMPipelineDTO]
    metadata: ResponseMetadata