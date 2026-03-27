from pydantic import BaseModel
from typing import Optional



class Node(BaseModel):
    id: str
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


class Segment(BaseModel):
    id: int
    from_node: Optional[str] = None 
    to_node: Optional[str] = None
    length_km: Optional[float] = None


class PipelineSegmentDTO(Segment):
    IGGIELGN_id: Optional[str] = None
    country_code_from: Optional[str] = None
    country_code_to: Optional[str] = None
    is_H_gas: bool = True
    geometry: dict | None = None