from typing import Optional
from app.schemas.base import Node, Segment

class MaritimeRouteSegment(Segment):
    """GeoJSON Geometry schema"""
    
    name: Optional[str] = None