
from typing import Optional
from pydantic import BaseModel

class ShippingLaneSegment(BaseModel):
    id: int
    from_node: Optional[int] = None
    to_node: Optional[int] = None
    distance_km: float
    geometry: dict | None = None