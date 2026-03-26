from pydantic import BaseModel, EmailStr
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
