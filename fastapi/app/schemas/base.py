

from typing import Optional
from pydantic import BaseModel


class Node(BaseModel):
    """Base schema for a node with latitude and longitude"""
    id: int
    lat: float
    lon: float

class Segment(BaseModel):
    """Base schema for a segment with optional start and end nodes"""
    id: int
    from_node: Optional[int] = None
    to_node: Optional[int] = None
    distance_km: Optional[float] = None
    geometry: Optional[dict] = None


class GeoJSONGeometry(BaseModel):
    """GeoJSON Geometry schema"""
    type: str
    coordinates: list

